Python 并发编程：Java 后端迁移笔记

并发最容易混淆的不是写法，而是“我到底在等什么”。等网络、等数据库，和不停地算一个大循环，适合的方案并不一样。写过 Java 线程池之后，尤其要留意两点：Python 多开线程不一定能多核计算，加上 `async` 也不会自动消除阻塞。

阅读顺序：1 分清概念 → 2 GIL 和锁 → 3 线程池 → 4 进程池 → 5 asyncio → 6 选型 → 7 后端边界 → 8 排错与测试 → 9 脚本输出 → 10 练习 → 11 自检。

本文以 CPython 3.11+ 的常见用法为主，GIL 相关结论针对默认启用 GIL 的构建，不能直接套到 free-threaded 构建上。先把常规环境中的三种方案弄清楚，再看自己的运行环境和依赖库。

先运行配套实验：

```powershell
python examples/concurrency_lab.py
```

脚本只使用标准库，以短暂的 `sleep` 模拟 I/O，并用小规模纯计算演示进程池；不访问网络，不写文件。

1）并发、并行、异步：先把三件事分开

1.1 轮流推进，不等于同时计算

- 并发：一段时间里，几个任务都在往前走。一个服务员在几桌之间来回处理，也算并发。
- 并行：同一时刻，几个任务确实在一起执行。几名厨师各自炒菜，才是并行；计算任务通常需要多个 CPU 核等条件。
- 异步：发起一件需要等待的事，不一直卡在那里等。`asyncio` 用事件循环安排任务，遇到需要等待的异步操作时，可以先让其他任务继续。

线程和进程由操作系统调度；单个 `asyncio` 事件循环中的任务主要靠协作切换。这里说的 `await` 也不是每次都会切换：如果等的结果已经准备好，当前任务可以直接继续。

1.2 对照 Java 时，哪些经验能用

可以把 Java 常见模型粗略映射为：

| Java 经验 | Python 对应 | 需要修正的直觉 |
| :-- | :-- | :-- |
| `ExecutorService` | `ThreadPoolExecutor` / `ProcessPoolExecutor` | 两种池解决的负载不同 |
| `CompletableFuture` | `Future`、`asyncio.Task` | `asyncio` 任务依赖事件循环运行 |
| WebFlux | `asyncio` 与异步 Web 框架 | 调用链中的库也必须非阻塞 |
| `synchronized` / `Lock` | `threading.Lock` / `asyncio.Lock` | 两类锁不能互换 |
| 多 JVM 实例 | `multiprocessing` | 进程内存隔离，参数通常需序列化 |
| try-with-resources 管线程池 | `with Executor(...)` | 离开代码块会关闭并等待池 |

2）GIL：限制常规线程的字节码并行，不负责业务安全

2.1 为什么纯 Python 循环多开线程，常常没有变快

在常规 CPython 3.11 进程中，GIL 这把解释器锁让同一时刻通常只有一个线程执行 Python 字节码。假如任务一直在做 Python 循环计算，两个线程就像轮流拿同一件工具：人多了，真正动手的仍通常只有一个，还多了交接成本。

等网络返回就不同了。线程等待 I/O 时通常会释放 GIL，其他线程可以趁这段空闲继续工作。所以“线程适合等待多的任务”和“纯 Python 计算通常不能靠线程吃满多核”并不矛盾。

GIL 不等于“Python 没有并发”，也不等于“代码天然线程安全”：

- 线程等待文件、网络、数据库等 I/O 时，CPython 会释放 GIL，其他线程可以推进，因此 I/O 密集任务常能从线程并发获益。
- 一些 C 扩展会在耗时本地计算时主动释放 GIL，是否能并行要查该库文档。
- 一行 Python 表达式可能包含多个字节码步骤；线程可能在步骤之间切换。
- 多个操作组成的“先检查、后修改”不是原子事务，即使每个单独容器操作看起来没出错也会有竞态。
- GIL 是解释器执行机制，不是业务数据的锁，更不能替代数据库事务或分布式锁。

判断时抓住两个词：纯 Python 计算、阻塞 I/O。前者在线程里通常难以多核并行，后者可以利用等待时间。至于本地扩展是否释放 GIL，要看具体库，不能只看外面写的是不是 Python。

马上练一下：把一个纯循环分别串行运行和放进两个线程运行，记录时间。再把循环换成两次 `sleep`，比较结果并解释差异。

2.2 为什么有 GIL，余额扣减仍然需要锁

看下面两步：“先看钱够不够，再扣钱”。它们合起来才是一次完整的业务操作：

```python
if account.balance >= amount:
    account.balance -= amount
```

如果两个线程都先看到余额充足，再分别扣款，就可能多扣。不能只锁住最后一次赋值，而要把“检查到扣减”整段放进同一把 `threading.Lock` 里：

```python
from threading import Lock


class Account:
    def __init__(self, balance: int) -> None:
        self.balance = balance
        self._lock = Lock()

    def withdraw(self, amount: int) -> bool:
        with self._lock:
            if self.balance < amount:
                return False
            self.balance -= amount
            return True
```

锁只解决同一进程内、共享同一对象的线程竞争。多进程或多机器部署中的余额一致性仍应依靠数据库事务、行锁、乐观锁或专门的分布式协调方案。

比如余额 100，两个线程都要取 80。没有业务锁时，可能出现：甲检查 100，乙也检查 100，甲扣完剩 20，乙仍根据刚才的检查继续扣，余额就可能出问题。加锁后，甲先完成“检查、扣款、释放锁”，乙才能进去；乙此时读到的是 20，就返回 False。

`with self._lock` 会在退出块时释放锁，包括从块里 `return False` 的情况，不用在每个分支手写 release。重点是两个线程操作同一个 Account，也使用同一把锁；各自临时创建一把锁，当然拦不住对方。这个片段只演示竞争控制，取款金额是否为正等输入规则还需另行校验。

3）线程池：现有代码经常等 I/O，就先考虑它

3.1 map 适合按输入顺序拿结果

已经有同步 HTTP、文件或数据库调用时，线程池往往改动较小。`ThreadPoolExecutor` 会管理工作线程，不需要你每收到一项任务就手动新建、回收一个 `Thread`。下面用短暂等待模拟远程读取：

```python
from concurrent.futures import ThreadPoolExecutor
from time import sleep


def read_remote(item_id: int) -> str:
    sleep(0.1)
    return f"item-{item_id}"


with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(read_remote, range(6)))

print(results)
```

`executor.map` 并发执行，但结果仍按输入顺序产出。某个任务抛出的异常会在调用方取到对应结果时重新抛出。

这一行的三个部分分别在做什么：`read_remote` 是要交给线程执行的函数，写函数名，不要提前加括号调用；`range(6)` 提供六个参数 0 到 5，每项对应一次 `read_remote(item_id)`；`max_workers=4` 表示最多四个工作线程同时处理，剩余工作等待线程空闲。

`executor.map(...)` 返回一个结果迭代器，外面的 `list(...)` 会逐项取结果并等待需要的结果到达。假如编号 0 最慢，编号 1 已经完成，也不会让 1 越过 0 出现在列表最前面。因此“任务完成顺序”和“结果交付顺序”是两件事。

3.2 submit 加 as_completed，谁先完成就先处理谁

如果第一个请求特别慢，按输入顺序取结果就要先等它。想让后面先完成的请求先交付，可以用 `submit` 拿到 Future，再通过 `as_completed` 逐个处理：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


with ThreadPoolExecutor(max_workers=4) as executor:
    future_to_id = {
        executor.submit(read_remote, item_id): item_id
        for item_id in range(6)
    }
    for future in as_completed(future_to_id):
        item_id = future_to_id[future]
        try:
            value = future.result()
        except Exception as exc:
            print(f"item {item_id} failed: {exc}")
        else:
            print(f"item {item_id}: {value}")
```

Future 可以理解成“稍后领取结果的凭据”。任务成功，`result()` 取回值；任务失败，`result()` 在调用方重新抛出异常。上面同时保存 `future_to_id`，是为了出错时还能知道失败的是哪项任务。

具体看 `executor.submit(read_remote, 2)`：提交时先返回一个 Future，不会在这一行等到 `read_remote(2)` 做完。`as_completed` 交出来的 Future 则已经结束，所以随后 `future.result()` 是取回结果或重新抛出它保存的异常。若不用 as_completed，直接对尚未结束的 Future 调用 result，调用它的线程就会等在那里。

3.3 线程数、取消和锁，都有各自的边界

- `max_workers` 不是越大越好。受外部连接池、服务限额、内存和上下文切换约束，应压测后决定。
- 使用 `with` 确保池被关闭。离开时默认等待已提交任务完成。
- `future.result()` 会等待并传播工作线程异常，不调用它可能让失败被忽略。
- `future.cancel()` 只能可靠取消尚未开始的任务，不能强杀正在执行的 Python 函数。
- 不要让线程池任务互相等待同一个小池里的其他任务，可能发生线程饥饿死锁。
- 跨线程传递工作可用线程安全的 `queue.Queue`，不要用无保护的列表模拟生产者消费者队列。
- 锁范围尽量小，但要包住必须一起完成的检查和修改；多把锁的获取顺序应固定，减少死锁。

线程池不是越大越快：数据库只给 10 个连接，开 100 个线程也不会变出 100 个连接。多出来的线程可能只是在等连接，还增加了内存和切换成本。先确定下游能承受多少，再决定开多少工作线程。

马上练一下：让 `read_remote(2)` 主动抛异常，分别用 `map` 和 `submit` 加 `as_completed` 执行，观察异常在主线程的哪个位置出现。

3.4 结果顺序和打印顺序，不要混为一谈

并发任务的打印顺序通常不稳定，测试不应断言日志先后。若业务需要与输入相同的结果顺序，使用 `executor.map` 或在结果中携带序号后排序；若追求低延迟流式处理，使用 `as_completed`。

4）进程池：任务一直在算，就把工作分给独立进程

4.1 每个进程单独工作，数据也要单独传递

在这里讨论的常规 CPython 环境中，`multiprocessing` 和 `ProcessPoolExecutor` 启动的每个进程都有自己的解释器、GIL 和内存。它们不必争同一把 GIL，因此能把纯 Python 计算分到多个 CPU 核上。

代价也很直接：启动进程需要时间，任务参数和结果通常要先序列化，再传过去。不是把线程池名字改成进程池，就一定更快。

```python
from concurrent.futures import ProcessPoolExecutor


def sum_of_squares(limit: int) -> int:
    return sum(number * number for number in range(limit))


def main() -> None:
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(sum_of_squares, [100_000, 120_000]))
    print(results)


if __name__ == "__main__":
    main()
```

进程版的参数和线程版类似，但有一道额外步骤：主进程把 `100_000` 这样的参数传给工作进程，工作进程调用 `sum_of_squares(100_000)`，计算完成再把整数结果送回。函数内部的普通局部变量属于工作进程，主进程拿到的是结果，不是共享了那段函数的运行现场。

4.2 Windows 为什么必须写 main guard

Windows 默认用 spawn 启动子进程，子进程会重新导入主模块。如果导入时就创建进程池，子进程也会照着再建一个池，可能反复启动进程，出现 `RuntimeError` 或负载暴涨。

`if __name__ == "__main__":` 就是在区分“直接运行这个文件”和“只是被导入”。把创建进程池和主流程放在保护内，只有直接启动的入口才执行它们。

另一个常见报错来自 `pickle`：进程池需要把工作交给另一个进程，lambda、局部函数和闭包通常无法按标准方式传过去。工作函数放在模块顶层，参数和返回值也要能序列化。

Windows 安全清单：

- 进程池创建和入口调用放在 main guard 内。
- 工作函数放模块顶层，参数和返回值保持可 pickle。
- 打包成可执行程序时常在入口调用 `multiprocessing.freeze_support()`。
- 不依赖子进程继承父进程中已打开的数据库连接、事件循环或锁。
- 避免在模块导入阶段执行网络请求、启动线程或创建进程。
- 在 IDE、Notebook 等交互环境中若序列化失败，优先把代码保存为 `.py` 文件从终端运行。

写进程池时先检查两处：工作函数是否在模块顶层，启动入口是否有 main guard。先把这两处写对，很多 Windows 上特有的困惑就能避开。

马上练一下：把进程工作函数临时移进 `main()`，在 Windows 运行并记录 pickle 错误，然后恢复到模块顶层。

4.3 子进程改了变量，为什么主进程没变化

子进程修改普通全局变量，不会自动反映到父进程。可选的进程间通信方式包括：

- `multiprocessing.Queue`：适合生产者消费者式消息传递。
- `multiprocessing.Pipe`：适合两个端点直接通信。
- `multiprocessing.Manager`：提供代理共享对象，方便但跨进程调用开销较高。
- `multiprocessing.shared_memory`：适合需要共享大块二进制数据的高级场景。
- Redis、消息队列或数据库：适合跨机器或需要持久性的系统。

一般先选“传入数据，计算，返回结果”，不要一开始就设计大家共同修改一堆变量。任务也不要切得太碎：一项只算一小会儿，却要花更久打包和传输，进程池反而慢。可以一次交给进程一批数据，把传递成本摊薄。

5）asyncio：等待的时候，让同一线程先做别的事

5.1 async def 创建协程，事件循环负责推进

普通函数调用后会执行函数体；`async def` 函数调用后，先得到的是协程对象。只有被 `await`、调度成 Task，或交给事件循环执行，它才会开始推进。只写一行 `fetch(1)` 然后不管它，不等于已经发起一次远程请求。

```python
import asyncio


async def fetch(item_id: int) -> str:
    await asyncio.sleep(0.1)
    return f"item-{item_id}"


async def main() -> None:
    results = await asyncio.gather(
        fetch(1),
        fetch(2),
        fetch(3),
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
```

`asyncio.run` 创建事件循环、运行顶层协程并完成清理，普通脚本通常只调用一次。已经运行事件循环的 Notebook 或异步框架内部应直接 `await main()`，不能嵌套调用 `asyncio.run()`。

先暂时放下 gather，单独看“创建协程”和“执行协程”的区别。下面这段可以单独存为 `.py` 文件运行：

```python
import asyncio


async def job(name: str) -> str:
    print(name, "start")
    await asyncio.sleep(0)
    print(name, "end")
    return name


async def main() -> None:
    pending = job("A")
    print("created")
    first = await pending
    second = await job("B")
    print(first, second)


asyncio.run(main())
```

输出顺序是 `created`、`A start`、`A end`、`B start`、`B end`、`A B`。

- `pending = job("A")` 只创建协程对象，所以还没打印 A start；名字叫 pending 还是别的，不改变这一点。
- `await pending` 才开始推进 A，并且 main 要等到 A 返回，才能给 first 赋值、执行下一行。
- A 中的 `await asyncio.sleep(0)` 主动给其他已调度任务运行的机会，但此时 B 还没有被创建，更没有被调度，所以不能趁机运行。
- A 完成以后，main 才执行 `await job("B")`。两行都写了 await，整个顺序依然是 A 完整结束，再轮到 B。

所以“函数里用了 await”和“几个任务已经并发运行”不能画等号。要让 A 等待时 B 也有机会执行，需要提前把两项工作都调度起来，见 5.3。

5.2 await 不是“把下一行扔到后台”

`await` 只能等待 awaitable，例如协程、Task 或 Future。它不是“把下一行放进后台”。当前任务遇到尚未完成的异步 I/O 时，把控制权交回事件循环；事件循环再推进其他就绪任务。

把事件循环看成一个负责多桌的服务员：这桌等菜时，服务员可以先去照顾别桌。但前提是等待方式能告诉他“现在可以离开，准备好后再回来”。普通阻塞函数做不到这一点，直接调用它，服务员就被钉在原地了。

如果在协程中写下面的代码，整个事件循环仍会被阻塞：

```python
import time


async def broken() -> None:
    time.sleep(2)
```

应优先使用真正的异步库；模拟等待用 `await asyncio.sleep(2)`。暂时无法替换的阻塞 I/O 函数，可以转到线程：

```python
result = await asyncio.to_thread(blocking_function, argument)
```

`to_thread` 主要适合阻塞 I/O，不会让受 GIL 限制的纯 Python CPU 循环神奇地多核并行。CPU 密集工作应考虑进程池、独立任务服务或释放 GIL 的本地库。

所以看一段代码是否适合放进协程，不是只看有没有 `async`，而是看里面有没有阻塞调用。旧的阻塞 I/O 暂时改不了，可以用 `to_thread` 转到线程；纯 Python 重计算则另想进程等方案。

马上练一下：同时启动一个每 0.1 秒打印一次的心跳协程和一个含 `time.sleep(1)` 的协程。观察心跳停顿，再改成 `await asyncio.sleep(1)`。

5.3 gather 收一组结果，Task 表示已调度的工作

`asyncio.gather(a(), b())` 会并发推进这两个可等待对象，结果按传入顺序返回。即使 b 先完成，结果仍是 `[a 的结果, b 的结果]`。

默认情况下，一个任务抛出异常，等待 `gather` 的调用方会立即收到该异常，但其他任务不会因此自动取消，仍可能继续。若取消的是 `gather` 本身，尚未完成的子任务会被取消。它负责一起等待，不负责像数据库事务一样“要么全成，要么撤销”。

`return_exceptions=True` 会把异常也放进结果列表。如果用了它，必须逐项区分成功值和异常，不能只为了“不报错”就打开这个选项。

`asyncio.create_task(coro())` 会把协程调度为 Task。应保存任务引用并在明确位置等待它；随手创建后台任务又不管理生命周期，异常和取消都很难处理。

把这几个名字分开就清楚了：协程对象是一份尚待推进的工作；Task 是事件循环已经接手管理的那份工作，里面会记录完成、失败或取消状态；`await task` 是当前协程等它的结果。等待者暂停，不代表整个线程原地阻塞，事件循环仍能推进其他就绪任务。

下面不用比较毫秒，也能确定 B 先完成、A 后完成。`Event` 只是一道通知：`wait()` 等通知，`set()` 发通知；没有设置时，等待它的协程会暂停。

```python
import asyncio


async def main() -> None:
    a_started = asyncio.Event()
    b_finished = asyncio.Event()
    trace: list[str] = []

    async def job_a() -> str:
        trace.append("A start")
        a_started.set()
        await b_finished.wait()
        trace.append("A end")
        return "A"

    async def job_b() -> str:
        await a_started.wait()
        trace.append("B start")
        trace.append("B end")
        b_finished.set()
        return "B"

    first = asyncio.create_task(job_a())
    second = asyncio.create_task(job_b())
    results = await asyncio.gather(first, second)
    print(trace)
    print(results)


asyncio.run(main())
```

两行输出分别是 `['A start', 'B start', 'B end', 'A end']` 和 `['A', 'B']`。

按过程看：main 调度两个任务，再等待 gather；A 发出“我开始了”的通知，然后等 B；B 收到通知后完成自己的工作，发出“我结束了”；A 才继续完成。B 先完成是 Event 之间的依赖保证的，不是靠机器恰好跑得快。

最后 gather 仍按 `first, second` 的传入顺序放结果，所以得到 A、B，不是 B、A。也可以直接把 `job_a()`、`job_b()` 传给 gather，它会把传入的协程调度为任务；单独调用这两个协程函数、把对象存进列表，却不会得到同样的执行效果。

再看一个故意失败的小实验。它保留了慢任务的引用，让你看到 gather 抛异常之后，慢任务到底是什么状态：

```python
import asyncio


async def main() -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow() -> str:
        started.set()
        await release.wait()
        return "slow finished"

    async def broken() -> None:
        await started.wait()
        raise ValueError("broken")

    slow_task = asyncio.create_task(slow())
    try:
        await asyncio.gather(slow_task, broken())
    except ValueError:
        print("caught error; slow done:", slow_task.done())
    release.set()
    print(await slow_task)


asyncio.run(main())
```

先输出 `caught error; slow done: False`，再输出 `slow finished`。broken 抛错后，main 离开 gather 进入 except，但 slow 仍在等 release，并没有自动取消。main 发通知后，slow 才继续返回；最后的 await 也明确收走它的结果。

如果 except 后直接结束 main，你可能反而看到慢任务被取消：那通常是 `asyncio.run` 在退出事件循环时清理剩余任务，不是 gather 的单任务失败自动取消了兄弟任务。区分“谁触发取消”，才能看懂实验输出。

5.4 TaskGroup 把一组任务的开始和收尾管在一起

Python 3.11 的 `asyncio.TaskGroup` 适合“几个任务共同完成一次操作”的情况。任务都放进同一个 `async with` 代码块，退出时统一等它们收尾；通常一个任务以非取消异常失败，就会取消其余任务，最后用异常组报告失败。这样不容易出现主流程已经结束、后台任务却无人管理的情况。

```python
import asyncio


async def load(name: str) -> str:
    await asyncio.sleep(0.05)
    return name.upper()


async def main() -> None:
    async with asyncio.TaskGroup() as group:
        first = group.create_task(load("users"))
        second = group.create_task(load("orders"))
    print(first.result(), second.result())
```

代码块正常退出，才可以像示例这样读取两个结果；如果失败，异常会走异常处理路径，不能当作两个任务都成功了。TaskGroup 会协调取消和等待，但也不会自动撤销任务已经写入的数据库数据。

上面先定义了 main，单独作为脚本运行时，要在末尾调用 `asyncio.run(main())`。`group.create_task(...)` 负责启动，退出 `async with` 负责统一等待；出了代码块再读 `first.result()`，正常路径下任务已经完成，所以这里不再需要 await。

下面用同样的“先等待，再故意失败”观察 TaskGroup 的不同。finally 用来证明慢任务确实经过了收尾：

```python
import asyncio


async def main() -> None:
    started = asyncio.Event()
    never_released = asyncio.Event()

    async def slow() -> None:
        try:
            started.set()
            await never_released.wait()
        finally:
            print("slow cleaned")

    async def broken() -> None:
        await started.wait()
        raise ValueError("broken")

    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(slow())
            group.create_task(broken())
    except* ValueError:
        print("group failed")


asyncio.run(main())
```

输出依次是 `slow cleaned`、`group failed`。broken 失败后，任务组请求取消 slow；slow 在等待位置收到取消，执行 finally；任务组等收尾完成，再把异常组交给外层。`except* ValueError` 处理异常组中对应的 ValueError，不是把整个组当成一个普通 ValueError。

这里慢任务没有吞掉取消，所以收尾能完成。如果任务卡在阻塞调用里，或捕获取消后继续不退出，TaskGroup 也不能凭空把它瞬间停掉。这就是为什么需要配合后面的超时和清理规则。

5.5 Semaphore 限制同时执行的数量，队列限制积压

能创建很多协程，不代表下游能同时处理很多请求。比如数据库只允许 20 个连接，就不该让几万个任务一起冲过去。`Semaphore` 像有限数量的通行证：拿到的才进入这段 I/O，其他任务先等着。

```python
import asyncio


async def limited_call(item_id: int, gate: asyncio.Semaphore) -> str:
    async with gate:
        await asyncio.sleep(0.05)
        return f"item-{item_id}"


async def main() -> None:
    gate = asyncio.Semaphore(20)
    results = await asyncio.gather(
        *(limited_call(item_id, gate) for item_id in range(100))
    )
    print(len(results))
```

这里有 100 个任务，但同一时刻最多 20 个进入 `async with gate`。注意，Semaphore 只限制同时进入的数量，不会减少已经创建的任务数。数据量很大时，还要用有界队列或分批提交，让生产方在积压过多时等一等；这就是“背压”。

配套 lab 把数量缩到 4 个任务、2 张通行证，更容易跟踪：两项任务拿到通行证，probe.active 从 0 增到 2；它们在 sleep 等待时仍占着通行证；其他任务等待，不能让 active 变成 3。已有任务经过 finally 减少 active，再退出 `async with gate` 归还通行证，后面的任务才有机会进去。具体哪项先拿到证不要当成业务保证，始终不超过 2 才是要验证的规则。

`probe.maximum_active` 记录的是“同时处在这段未完成 I/O 中的任务数”，不是“同一时刻有几个协程在 CPU 上运行”。单线程事件循环里，两项等待可以重叠，Python 代码仍是轮流执行。

上限要一起看 HTTP 客户端、数据库连接池和下游配额。所谓“单线程支撑十万连接”依赖具体负载、操作系统和内存条件，不是加上 `asyncio` 就能得到的保证。

5.6 超时之后，还要把连接和锁还回去

Python 3.11 可用 `asyncio.timeout` 给一段等待设置边界：

```python
import asyncio


async def main() -> None:
    try:
        async with asyncio.timeout(0.2):
            await asyncio.sleep(1)
    except TimeoutError:
        print("timed out")
```

取消不是把正在执行的函数从中间强行抹掉。它通常在 `await` 点通过 `asyncio.CancelledError` 通知协程“该停下了”。用 `try/finally` 或异步上下文管理器释放连接、归还锁；如果专门捕获了 `CancelledError` 做清理，清理后通常还要 `raise`，让上层知道取消没有被悄悄吃掉。

上面 timeout 片段的顺序是：进入范围并开始计时；sleep 还没完成时达到 0.2 秒，当前等待被取消；退出 timeout 上下文后，外层收到 `TimeoutError`，于是打印 timed out。不要把它理解成 sleep 自动改成了 0.2 秒后正常返回。单独运行这段定义时，同样要在末尾加 `asyncio.run(main())`。

`CancelledError` 和一般业务错误也要分开对待。在这里使用的 Python 版本中，它继承自 BaseException，普通 `except Exception` 通常不会抓住它；容易吞掉它的是裸 `except`、`except BaseException`，或者专门捕获后没有重新抛出。清理放 finally，通常更不容易写错。

`asyncio.Lock` 只用于同一事件循环内协程之间的状态协调，不是线程锁，也不能跨进程。临界区内不能执行长时间阻塞操作，否则虽然拿了“异步锁”，事件循环仍被冻住。

6）怎么选：先判断是在计算，还是在等待

| 负载与约束 | 首选 | 原因 | 常见替代 |
| :-- | :-- | :-- | :-- |
| 已有同步 HTTP/文件/数据库客户端，I/O 较多 | 线程池 | 改造成本低，等待时可并发 | 逐步改成异步客户端 |
| 纯 Python 图像处理、压缩计算、复杂循环 | 多进程 | 独立 GIL，可多核并行 | 本地扩展、独立任务服务 |
| 大量连接，调用链已有异步驱动 | `asyncio` | 单线程协作调度，任务开销较低 | 多进程运行多个事件循环实例 |
| 少量简单任务 | 串行 | 并发启动和协调也有成本 | 无需为了形式引入并发 |
| NumPy 等本地库计算 | 先查库行为并压测 | 本地代码可能释放 GIL 或自己开线程 | 控制库线程数或用进程 |

可以先记一条简短判断：纯 Python 算得久，考虑进程；同步 I/O 等得久，考虑线程；连接多、整条调用链都支持异步，考虑协程。任务很少时，串行往往已经足够。

实际后端常把它们混用：多个 Web 服务进程，各自运行事件循环；少量旧的阻塞 I/O 交给受控线程池；重计算交给独立工作进程。它们不是三选一的阵营，而是解决不同部分的问题。

7）放进后端服务后，还要一起算下游的承受能力

- 在 FastAPI 的 `async def` 路由里调用同步数据库驱动或 `requests`，会阻塞该 worker 的事件循环。应使用异步驱动，或明确转线程。
- 异步不会扩大数据库连接池。即使创建一万协程，也应通过连接池和信号量控制数据库并发。
- 不要为每个 HTTP 请求临时创建进程池，进程启动成本很高；通常复用池或交给 Celery 等独立任务系统。
- Web worker 数、每 worker 线程数、数据库连接数和下游限额要一起核算，避免层层放大并发。
- 请求超时不代表下游操作已自动取消。要确认客户端库的取消语义，并设置连接、读取和整体超时。
- CPU 使用率低不必然说明需要更多并发，可能是在等待数据库锁、连接池或外部限流。

8）排错和测试：先看结果有没有被领取

8.1 提交了任务，也要接住它的结果和异常

线程池和进程池把异常保存在 Future 中，调用 `result()` 时重新抛出。进程异常需要序列化，堆栈与自定义异常对象可能受 pickle 限制。

`asyncio` 任务的异常应由 `await`、`gather` 或 TaskGroup 明确收集。出现 “Task exception was never retrieved” 往往说明创建了任务却没人等待它，不应只靠加日志压掉警告。

8.2 测试确定的结果，不猜任务碰巧先后执行

- 不用 `sleep` 猜测任务一定已经执行；线程测试可使用 `Event`、`Barrier`，协程测试可等待明确状态。
- 测试业务结果和必须一直成立的规则，例如余额不能为负、并发数不超上限；少断言日志先后。
- 给测试设置超时，避免死锁让测试套件永久挂起。
- 把进程工作函数放在可导入模块顶层，Windows CI 也运行一遍。
- 性能测试区分冷启动与稳定阶段，记录任务规模、worker 数、CPU 核数和外部资源上限。
- 用足够大的 CPU 任务评估进程池，否则测到的主要是启动与序列化开销。

8.3 常见现象与第一检查点

- 用线程加速纯 Python CPU 循环：GIL 下通常无收益；改用进程或释放 GIL 的库。
- 认为有 GIL 就不需要锁：连续的读取、判断、修改仍可能被其他线程插入；要保护完整操作。
- Windows 没有 main guard 就创建进程：子进程重复导入并再次建池；把入口放进保护块。
- 把 lambda、局部函数或带不可序列化状态的对象提交进程池：pickle 失败；工作函数放模块顶层，参数简化。
- 在 `async def` 中调用 `time.sleep` 或同步 HTTP 客户端：冻结事件循环；换异步 API 或 `to_thread`。
- 调用协程函数却不 `await`：函数体没有运行并可能出现 “coroutine was never awaited” 警告。
- 无限创建 Task：内存或下游先被压垮；使用有界队列、批处理或 Semaphore。
- 混用 `threading.Lock` 与 `asyncio.Lock`：等待机制不兼容，可能阻塞事件循环。
- 捕获所有异常后吞掉 `CancelledError`：服务停机和超时无法及时传播；清理后继续抛出取消。
- 只提交 Future 不读取结果：工作任务异常悄悄积累；统一收集和记录结果。
- 在进程之间假设全局缓存共享：每个进程有独立副本；显式设计 IPC 或外部存储。

9）运行配套脚本，哪些输出应该一致

具体耗时因电脑而异，但结果内容应保持一致，末尾应看到：

```text
thread pool
thread results: ['io-0', 'io-1', 'io-2', 'io-3']
protected counter: 4000

process pool
process checksums: [46560000, 55872000]

asyncio
gather results: ['async-0', 'async-1', 'async-2', 'async-3']
maximum active async jobs: 2
blocking bridge result: blocking-ok
timeout handled: timed out

all concurrency assertions passed
```

进程校验值来自固定输入；这个脚本使用的线程池 `map` 和 `gather` 都按输入顺序返回结果。脚本会断言检查锁保护、并发上限、超时和返回顺序，耗时略有变化不代表出错。

10）动手练习：一次只改变一个条件

10.1 把线程实验的 `max_workers` 分别改成 1、2、4、8，记录总耗时。说明为什么模拟 I/O 会先加速，worker 继续增长后收益逐渐减小。

10.2 暂时移除计数器的锁并重复运行，观察最终值是否稳定。不要以某一次“刚好正确”证明线程安全；记录每种结果出现了几次，再恢复锁。

10.3 保持总循环次数相同，对比进程池接收 2 个大任务和 200 个小任务时的耗时，解释打包传输和调度为什么也要花时间。

10.4 实现异步批量处理器，最多同时运行 5 个任务，单任务超时 0.2 秒。返回成功值与失败原因，但不要把异常对象误当正常字符串。

10.5 在 TaskGroup 中让一个任务故意失败，给其他任务加入 `try/finally` 清理日志，观察取消传播和 `ExceptionGroup`。使用 `except* ValueError` 只处理对应异常。

10.6 把一个同步函数分别通过直接调用和 `asyncio.to_thread` 调用，同时运行心跳协程。比较心跳是否被阻塞，并解释 `to_thread` 为什么适合 I/O 而非纯 Python CPU 加速。

10.7 设计一个订单导入流程：读 100 个文件、解析 CPU 密集格式、异步写数据库。分别说明线程、进程和协程负责哪一步，以及队列满了之后，如何让上游暂缓继续提交。

11）合上代码，检查自己能否讲清楚

- 能解释并发、并行和异步的区别。
- 能准确描述常规 CPython 的 GIL，并说明它为什么不等于线程安全。
- 能用线程池处理阻塞 I/O，并通过 Future 传播异常。
- 能用锁保护完整的“先检查、再修改”，而不只保护最后一次赋值。
- 能写出 Windows 安全的进程池 main guard 和模块顶层工作函数。
- 能解释进程独立内存、pickle 限制和 IPC 成本。
- 能区分协程对象与 Task，知道协程要被等待或调度，函数体才会推进。
- 能识别事件循环中的阻塞调用，并选择异步库或 `to_thread`。
- 能用 `gather`、TaskGroup、Semaphore 和 timeout 管理生命周期、并发量与失败。
- 能根据 CPU 密集、传统 I/O 和全异步 I/O 负载选择合适模型。

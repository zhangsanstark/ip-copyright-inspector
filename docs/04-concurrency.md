Python 并发编程：Java 后端迁移笔记

这份笔记围绕 CPython 3.11+ 的线程、进程和 `asyncio` 展开。Java 后端开发者需要特别调整两个直觉：线程不一定带来 Python 字节码的 CPU 并行；协程也不会自动把阻塞代码变成非阻塞代码。

先用餐厅来理解：

- 线程像同一间厨房里的多名服务员。有人等顾客点菜时，别人可以继续送餐；但大家仍会争用同一套关键设备。
- 进程像开了多间独立厨房。每间都有自己的设备，能同时炒菜，但传菜和沟通更贵。
- `asyncio` 像一名非常会安排顺序的服务员。他记录许多桌的状态，某桌在等菜时马上服务下一桌；如果这名服务员自己跑去慢慢炒菜，所有桌都会停住。

比喻只帮助入门，下面每节都会补上准确边界。

先运行配套实验：

```powershell
python examples/concurrency_lab.py
```

脚本只使用标准库，以短暂的 `sleep` 模拟 I/O，并用小规模纯计算演示进程池；不访问网络，不写文件。

并发、并行与异步不是同义词

- 并发表示多个任务在一段时间内都有进展，可能轮流执行。
- 并行表示多个任务在同一时刻真正执行，需要多个 CPU 核、多个进程或能脱离 GIL 的本地代码等条件。
- 异步是一种协作式并发组织方式。任务在 `await` 可等待操作时主动交还控制权。
- 线程和进程是操作系统调度的执行单元；`asyncio` 任务主要由单个事件循环协作调度。

可以把 Java 常见模型粗略映射为：

| Java 经验 | Python 对应 | 需要修正的直觉 |
| :-- | :-- | :-- |
| `ExecutorService` | `ThreadPoolExecutor` / `ProcessPoolExecutor` | 两种池解决的负载不同 |
| `CompletableFuture` | `Future`、`asyncio.Task` | `asyncio` 任务依赖事件循环运行 |
| WebFlux | `asyncio` 与异步 Web 框架 | 调用链中的库也必须非阻塞 |
| `synchronized` / `Lock` | `threading.Lock` / `asyncio.Lock` | 两类锁不能互换 |
| 多 JVM 实例 | `multiprocessing` | 进程内存隔离，参数通常需序列化 |
| try-with-resources 管线程池 | `with Executor(...)` | 离开代码块会关闭并等待池 |

GIL 的准确理解

在常规 CPython 3.11 进程中，全局解释器锁 GIL 保证同一时刻通常只有一个线程执行 Python 字节码。因此，纯 Python 的 CPU 密集循环放进更多线程，通常不能把多个 CPU 核吃满，还会增加调度和争锁成本。

把 GIL 想成同一间厨房里唯一的一把“Python 操作钥匙”。服务员可以很多，但执行纯 Python 操作时通常只有拿到钥匙的人能动手。有人去等外卖、等水开，也就是等待 I/O 时，会把钥匙交出来。

GIL 不等于“Python 没有并发”，也不等于“代码天然线程安全”：

- 线程等待文件、网络、数据库等 I/O 时，CPython 会释放 GIL，其他线程可以推进，因此 I/O 密集任务常能从线程并发获益。
- 一些 C 扩展会在耗时本地计算时主动释放 GIL，是否能并行要查该库文档。
- 一行 Python 表达式可能包含多个字节码步骤；线程可能在步骤之间切换。
- 多个操作组成的“先检查、后修改”不是原子事务，即使每个单独容器操作看起来没出错也会有竞态。
- GIL 是解释器执行机制，不是业务数据的锁，更不能替代数据库事务或分布式锁。

记忆口诀：GIL 限字节码，不包业务安全；等待 I/O 可让路，纯 Python 计算线程难并行。

马上练一下：把一个纯循环分别串行运行和放进两个线程运行，记录时间。再把循环换成两次 `sleep`，比较结果并解释差异。

经典竞态是余额扣减：

```python
if account.balance >= amount:
    account.balance -= amount
```

两个线程可能都在检查时看到余额充足，然后重复扣减。进程内共享状态可用同一把 `threading.Lock` 保护完整临界区：

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

线程：传统阻塞 I/O 的实用方案

标准库推荐优先使用 `concurrent.futures.ThreadPoolExecutor`，比手动创建和回收大量 `Thread` 更容易管理异常和结果。

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

若要按完成顺序处理，并单独识别每个任务，可配合 `submit` 与 `as_completed`：

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

线程池实践要点：

- `max_workers` 不是越大越好。受外部连接池、服务限额、内存和上下文切换约束，应压测后决定。
- 使用 `with` 确保池被关闭。离开时默认等待已提交任务完成。
- `future.result()` 会等待并传播工作线程异常，不调用它可能让失败被忽略。
- `future.cancel()` 只能可靠取消尚未开始的任务，不能强杀正在执行的 Python 函数。
- 不要让线程池任务互相等待同一个小池里的其他任务，可能发生线程饥饿死锁。
- 跨线程传递工作可用线程安全的 `queue.Queue`，不要用无保护的列表模拟生产者消费者队列。
- 锁范围尽量小，但必须覆盖完整不变量；锁顺序应固定，减少死锁。

生活类比：线程池像固定数量的窗口。任务排队等窗口，不需要每来一个顾客就临时盖一间窗口。窗口太少会排长队，太多又会争抢场地和后端资源。

记忆口诀：阻塞 I/O 找线程，结果异常找 Future，共享读改写要锁完整一段。

马上练一下：让 `read_remote(2)` 主动抛异常，分别用 `map` 和 `submit` 加 `as_completed` 执行，观察异常在主线程的哪个位置出现。

线程示例中的输出顺序

并发任务的打印顺序通常不稳定，测试不应断言日志先后。若业务需要与输入相同的结果顺序，使用 `executor.map` 或在结果中携带序号后排序；若追求低延迟流式处理，使用 `as_completed`。

进程：绕开单进程 GIL 做 CPU 并行

`multiprocessing` 和 `ProcessPoolExecutor` 会启动独立进程，每个进程有自己的解释器、GIL 和内存空间。纯 Python CPU 密集任务可以在多核上真正并行，但要支付启动、序列化和进程间通信成本。

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

Windows 默认使用 spawn 方式启动子进程。子进程会重新导入主模块，因此创建进程池和调用主流程必须放在 `if __name__ == "__main__":` 保护内。否则可能递归启动进程，出现 RuntimeError 或机器负载暴涨。可提交给进程池的工作函数也应定义在模块顶层，lambda、局部函数和闭包通常无法被标准 `pickle` 正确序列化。

Windows 安全清单：

- 进程池创建和入口调用放在 main guard 内。
- 工作函数放模块顶层，参数和返回值保持可 pickle。
- 打包成可执行程序时常在入口调用 `multiprocessing.freeze_support()`。
- 不依赖子进程继承父进程中已打开的数据库连接、事件循环或锁。
- 避免在模块导入阶段执行网络请求、启动线程或创建进程。
- 在 IDE、Notebook 等交互环境中若序列化失败，优先把代码保存为 `.py` 文件从终端运行。

生活类比：Windows 子进程像拿着脚本复印件从第一页重新读。如果第一页读到“立刻再开两个子进程”，复印件也会继续复印，形成失控循环。main guard 就是在说“只有原始入口能按下启动按钮”。

记忆口诀：进程算 CPU，函数放顶层，Windows 入口必须守门。

马上练一下：把进程工作函数临时移进 `main()`，在 Windows 运行并记录 pickle 错误，然后恢复到模块顶层。

独立内存意味着什么

子进程修改普通全局变量，不会自动反映到父进程。可选的进程间通信方式包括：

- `multiprocessing.Queue`：适合生产者消费者式消息传递。
- `multiprocessing.Pipe`：适合两个端点直接通信。
- `multiprocessing.Manager`：提供代理共享对象，方便但跨进程调用开销较高。
- `multiprocessing.shared_memory`：适合需要共享大块二进制数据的高级场景。
- Redis、消息队列或数据库：适合跨机器或需要持久性的系统。

优先传递消息和返回结果，少共享可变状态。进程池收到的每个参数和返回值通常需要序列化；如果单个任务太小，序列化与调度成本可能比计算本身更大。可通过批量分块提高粒度。

`asyncio`：单线程协作式 I/O 并发

`async def` 调用后不会立刻执行函数体，而是返回协程对象。协程只有被 `await`、包装成任务，或传给事件循环后才会推进。

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

`await` 的真实含义

`await` 只能等待 awaitable，例如协程、Task 或 Future。它不是“把下一行放进后台”。当前任务遇到尚未完成的异步 I/O 时，把控制权交回事件循环；事件循环再推进其他就绪任务。

生活类比：`await` 不是增加服务员，而是当前桌说“菜好之前你先去忙别桌”。只有等待对象真的支持稍后通知，服务员才能离开。普通耗时函数不会自动发通知，所以直接调用仍会堵住服务员。

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

记忆口诀：`async def` 只造协程，`await` 才推进；协程里别阻塞，旧 I/O 可暂送线程。

马上练一下：同时启动一个每 0.1 秒打印一次的心跳协程和一个含 `time.sleep(1)` 的协程。观察心跳停顿，再改成 `await asyncio.sleep(1)`。

`gather`、Task 与结果顺序

`asyncio.gather(a(), b())` 并发推进多个 awaitable，并按传入顺序返回结果，与实际完成顺序无关。默认情况下某个 awaitable 抛异常时，等待 `gather` 的调用方会收到该异常；不要仅为“不中断”就随意使用 `return_exceptions=True`，否则异常会混入结果列表，很容易被当成正常值。

`asyncio.create_task(coro())` 会把协程调度为 Task。应保存任务引用并在明确位置等待它；随手创建后台任务又不管理生命周期，异常和取消都很难处理。

Python 3.11 的结构化并发

`asyncio.TaskGroup` 将一组子任务绑定到代码块生命周期。一个任务失败时，其余任务会被取消，退出代码块时以异常组报告失败，适合“这些任务共同组成一次操作”的场景。

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

任务组退出后，两个任务要么完成，要么失败路径已统一处理。它比维护一批无人负责的后台 Task 更容易推理。

限流与背压

协程很轻量，但一次性创建几十万个任务仍会占用内存，并可能瞬间压垮数据库连接池或下游服务。`Semaphore` 可以限制同时进入某段 I/O 的任务数：

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

并发连接上限应与 HTTP 客户端、数据库连接池及下游配额共同设计。所谓“单线程支撑十万连接”是特定负载、操作系统和内存条件下的容量描述，不是任何业务都能直接达到的保证。

超时、取消与清理

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

取消通常通过在 `await` 点抛出 `asyncio.CancelledError` 传递。协程应使用 `try/finally` 或异步上下文管理器释放连接和锁，不要无意吞掉取消。若确实捕获 `CancelledError` 做清理，清理后通常要再次 `raise`。

`asyncio.Lock` 只用于同一事件循环内协程之间的状态协调，不是线程锁，也不能跨进程。临界区内不能执行长时间阻塞操作，否则虽然拿了“异步锁”，事件循环仍被冻住。

三种模型如何选

| 负载与约束 | 首选 | 原因 | 常见替代 |
| :-- | :-- | :-- | :-- |
| 已有同步 HTTP/文件/数据库客户端，I/O 较多 | 线程池 | 改造成本低，等待时可并发 | 逐步改成异步客户端 |
| 纯 Python 图像处理、压缩计算、复杂循环 | 多进程 | 独立 GIL，可多核并行 | 本地扩展、独立任务服务 |
| 大量连接，调用链已有异步驱动 | `asyncio` | 单线程协作调度，任务开销较低 | 多进程运行多个事件循环实例 |
| 少量简单任务 | 串行 | 并发启动和协调也有成本 | 无需为了形式引入并发 |
| NumPy 等本地库计算 | 先查库行为并压测 | 本地代码可能释放 GIL 或自己开线程 | 控制库线程数或用进程 |

口诀可以记作：纯 Python CPU 密集优先多进程；传统阻塞 I/O 优先线程；全链路非阻塞的高并发 I/O 优先 `asyncio`。真实后端常混合使用，例如多个 Web 服务进程各自运行一个事件循环，将少量遗留阻塞 I/O 送入受控线程池，再把重 CPU 任务交给独立工作进程。

更短的选择口诀：算得久用进程，等得久用线程，连接多且全异步用协程；任务很少先串行。

后端工程中的边界

- 在 FastAPI 的 `async def` 路由里调用同步数据库驱动或 `requests`，会阻塞该 worker 的事件循环。应使用异步驱动，或明确转线程。
- 异步不会扩大数据库连接池。即使创建一万协程，也应通过连接池和信号量控制数据库并发。
- 不要为每个 HTTP 请求临时创建进程池，进程启动成本很高；通常复用池或交给 Celery 等独立任务系统。
- Web worker 数、每 worker 线程数、数据库连接数和下游限额要一起核算，避免层层放大并发。
- 请求超时不代表下游操作已自动取消。要确认客户端库的取消语义，并设置连接、读取和整体超时。
- CPU 使用率低不必然说明需要更多并发，可能是在等待数据库锁、连接池或外部限流。

异常处理的对照

线程池和进程池把异常保存在 Future 中，调用 `result()` 时重新抛出。进程异常需要序列化，堆栈与自定义异常对象可能受 pickle 限制。

`asyncio` 任务的异常应由 `await`、`gather` 或 TaskGroup 明确收集。出现 “Task exception was never retrieved” 往往说明创建了任务却没人等待它，不应只靠加日志压掉警告。

并发测试方法

- 不用 `sleep` 猜测任务一定已经执行；线程测试可使用 `Event`、`Barrier`，协程测试可等待明确状态。
- 测试业务结果和不变量，少断言并发日志顺序。
- 给测试设置超时，避免死锁让测试套件永久挂起。
- 把进程工作函数放在可导入模块顶层，Windows CI 也运行一遍。
- 性能测试区分冷启动与稳定阶段，记录任务规模、worker 数、CPU 核数和外部资源上限。
- 用足够大的 CPU 任务评估进程池，否则测到的主要是启动与序列化开销。

常见错误与排查

- 用线程加速纯 Python CPU 循环：GIL 下通常无收益；改用进程或释放 GIL 的库。
- 认为有 GIL 就不需要锁：复合读改写仍有竞态；保护业务不变量。
- Windows 没有 main guard 就创建进程：子进程重复导入并再次建池；把入口放进保护块。
- 把 lambda、局部函数或带不可序列化状态的对象提交进程池：pickle 失败；工作函数放模块顶层，参数简化。
- 在 `async def` 中调用 `time.sleep` 或同步 HTTP 客户端：冻结事件循环；换异步 API 或 `to_thread`。
- 调用协程函数却不 `await`：函数体没有运行并可能出现 “coroutine was never awaited” 警告。
- 无限创建 Task：内存或下游先被压垮；使用有界队列、批处理或 Semaphore。
- 混用 `threading.Lock` 与 `asyncio.Lock`：等待机制不兼容，可能阻塞事件循环。
- 捕获所有异常后吞掉 `CancelledError`：服务停机和超时无法及时传播；清理后继续抛出取消。
- 只提交 Future 不读取结果：工作任务异常悄悄积累；统一收集和记录结果。
- 在进程之间假设全局缓存共享：每个进程有独立副本；显式设计 IPC 或外部存储。

配套脚本的预期输出结构

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

进程校验值来自固定输入；线程池和 `gather` 都按输入顺序返回结果。脚本用断言检查锁保护、并发上限、超时和返回顺序。

动手练习

练习一：把线程实验的 `max_workers` 分别改成 1、2、4、8，记录总耗时。说明为什么模拟 I/O 会先加速，worker 继续增长后收益逐渐减小。

练习二：暂时移除计数器的锁并重复运行，观察最终值是否稳定。不要以某一次“刚好正确”证明线程安全；把每次运行结果统计成分布，再恢复锁。

练习三：为进程池增加不同任务粒度。保持总循环次数相同，对比 2 个大任务和 200 个小任务，解释序列化与调度成本。

练习四：实现异步批量处理器，最多同时运行 5 个任务，单任务超时 0.2 秒。返回成功值与失败原因，但不要把异常对象误当正常字符串。

练习五：在 TaskGroup 中让一个任务故意失败，给其他任务加入 `try/finally` 清理日志，观察取消传播和 `ExceptionGroup`。使用 `except* ValueError` 只处理对应异常。

练习六：把一个同步函数分别通过直接调用和 `asyncio.to_thread` 调用，同时运行心跳协程。比较心跳是否被阻塞，并解释 `to_thread` 为什么适合 I/O 而非纯 Python CPU 加速。

练习七：设计一个订单导入流程：读 100 个文件、解析 CPU 密集格式、异步写数据库。分别给出线程、进程和协程所在位置，并说明队列容量如何形成背压。

自检清单

- 能解释并发、并行和异步的区别。
- 能准确描述常规 CPython 的 GIL，并说明它为什么不等于线程安全。
- 能用线程池处理阻塞 I/O，并通过 Future 传播异常。
- 能用锁保护完整读改写不变量，而不只保护单次赋值。
- 能写出 Windows 安全的进程池 main guard 和模块顶层工作函数。
- 能解释进程独立内存、pickle 限制和 IPC 成本。
- 能区分协程对象与 Task，知道 `await` 才会让协程推进。
- 能识别事件循环中的阻塞调用，并选择异步库或 `to_thread`。
- 能用 `gather`、TaskGroup、Semaphore 和 timeout 管理生命周期、并发量与失败。
- 能根据 CPU 密集、传统 I/O 和全异步 I/O 负载选择合适模型。

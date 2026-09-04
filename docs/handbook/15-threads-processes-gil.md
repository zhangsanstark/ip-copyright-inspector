15 线程、进程与 GIL：谁在等，谁在算，谁在改同一份数据

并发代码难的地方，不在于多写几个启动函数，而在于事情不再按一条直线发生。必须明确每项工作什么时候开始、结果由谁领取、失败怎样传回来、共享数据怎样保持一致。

阅读路线：1 选择线程还是进程 → 2 GIL 的适用范围 → 3 竞争与锁 → 4 线程池与异常 → 5 Windows 进程池 → 6 IPC → 7 练习及答案。

所有 runnable 块只用标准库。运行 `python scripts/check_handbook_examples.py --chapter 15 --show-output`。进程示例应保存成真实 `.py` 执行，不要拆进交互式窗口，也不要删掉 main 保护。示例不访问网络、不启动外部服务。

---

1）先拆工作，再选择并发方式

1.1 并发和并行不是一回事

并发强调多项工作在同一段时间内都能向前推进。一项工作等文件或网络时，另一项可以运行。

并行强调同一时刻真的有多项计算在执行，比如两个 CPU 核心各跑一份计算。

一个线程也能通过事件循环管理多项等待中的工作；很多线程也可能受某个锁限制，一次只有一个在执行关键代码。不能只看“启动了几个”就判断实际并行度。

1.2 Java 线程池经验哪些还能沿用

任务要提交、Future 要取结果、共享数据要同步、池需要关闭，这些经验都能继续用。

差别主要在纯 Python CPU 计算的并行方式。对启用 GIL 的常规 CPython，多线程通常不能让多个核心同时执行同一进程里的纯 Python 字节码；独立进程更适合这类计算并行。

| 任务大部分时间在做什么 | 常见起点 | 先检查什么 |
| :-- | :-- | :-- |
| 同步网络、文件等阻塞 I/O | 线程池 | 客户端是否线程安全，连接数是否够 |
| 大段纯 Python 计算 | 进程池 | 任务是否足够大，参数能否序列化 |
| 已有异步客户端的大量 I/O | asyncio | 整条调用链是否真的非阻塞 |
| 本地扩展库计算 | 看库行为再测量 | 是否释放 GIL，是否已经内部开线程 |
| 几个很小的操作 | 先串行 | 并发启动成本是否超过工作本身 |

---

2）GIL 是解释器边界，不是业务锁

2.1 本章说的是哪种运行环境

这里讨论的是常规、启用 GIL 的 CPython。它让同一进程同一时刻通常只有一个线程执行 Python 字节码。阻塞 I/O 和部分本地扩展可以释放 GIL，因此线程仍然适合重叠 I/O 等待。

这不等于“所有 Python 实现永远只能用一个核”，也不等于“NumPy 的所有计算都由这个结论直接决定”。扩展库可以在本地代码中释放 GIL，自己也可能管理多线程。

另外，CPython 存在可选的 free-threaded 构建。是否启用、依赖扩展是否支持、运行时是否重新启用 GIL，都要看实际环境，不能只看源码中 import 了什么就下结论。本章示例不用 free-threaded 专属接口，也不假定读者已经启用它。[官方 free-threading 说明](https://docs.python.org/3/howto/free-threading-python.html)

2.2 “某一步不同时执行”不等于“整个业务动作不可插队”

扣库存常常是三步：读取库存、判断够不够、保存扣减后库存。即使底层保证某个单独操作不会把解释器弄坏，也不代表这三步会作为一个整体完成。

线程 A 读完以后，线程 B 可以也读一次。两者都可能根据旧值做判断，再各自写入结果。

因此不能用 GIL 替代 threading.Lock。即使换到 free-threaded 环境，共享业务状态的完整约束也仍需要同步设计。

---

3）看见一次确定会发生的丢失更新

3.1 不靠“碰巧调度”，用 Barrier 安排插队位置

```python
# runnable: hb15_lost_update
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier


state = {"value": 0}
both_read = Barrier(2)


def unsafe_increment() -> int:
    previous = state["value"]
    both_read.wait(timeout=5)
    state["value"] = previous + 1
    return previous


with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(unsafe_increment) for _ in range(2)]
    previous_values = [future.result(timeout=10) for future in futures]

assert previous_values == [0, 0]
assert state["value"] == 1
print(previous_values, state["value"])
```

两个任务先各自读取 0，然后在 Barrier 汇合。必须两者都读完，才会继续写入。因此两人都计算 `0 + 1`，最后结果是 1，而不是 2。

Barrier 不是保护数据的锁，它在这里专门制造“两个任务都拿到旧值”的局面。测试不需要押注某个 Python 版本是否在 `+=` 的某个位置切换线程。

有时去掉锁跑一万次也没碰到错误，这只能说明那一万次调度没触发问题，不能证明逻辑安全。正确性应该来自完整同步，而不是来自某次运行运气好。

3.2 用同一把锁保护完整修改

```python
# runnable: hb15_locked_counter
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class Counter:
    def __init__(self) -> None:
        self._value = 0
        self._lock = Lock()

    def increment(self) -> None:
        with self._lock:
            self._value += 1

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


counter = Counter()


def work(times: int) -> None:
    for _ in range(times):
        counter.increment()


with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(work, 1000) for _ in range(4)]
    for future in futures:
        future.result(timeout=10)

assert counter.value == 4000
print(counter.value)
```

锁属于 counter 实例，因此四个任务争用同一把锁。如果每次进入 increment 都临时创建 `Lock()`，大家拿的是不同的锁，就没有互斥效果。

`with self._lock` 会在离开时释放锁，包括 return 或抛异常离开。它只管理锁的释放，不会自动撤销临界区已经完成的写入。

对于扣库存，应把“判断库存够不够”和“保存新库存”一起放在锁里，而不是只锁最后的减法。

3.3 临界区越小越好，但不能小到破坏约束

锁里尽量只做必须一起完成的检查和状态修改。不要拿着锁执行长时间网络请求，导致其他任务全在等。

不过，把检查挪到锁外只是为了缩短时间，可能又把竞争带回来。先定义必须保持的业务规则，再决定锁范围。

同一线程重复获取普通 Lock 可能让自己卡住。RLock 允许同一线程重入，但不是所有死锁的通用解药。多把锁还需要固定获取顺序，避免 A 拿着第一把等第二把、B 拿着第二把等第一把。

---

4）线程池：提交不是完成，取结果才看见失败

4.1 map 按输入顺序交回结果

```python
# runnable: hb15_thread_map
from concurrent.futures import ThreadPoolExecutor
from time import sleep


def read_record(number: int) -> str:
    sleep(0.01)
    return f"record-{number}"


with ThreadPoolExecutor(max_workers=2) as pool:
    result_iterator = pool.map(read_record, [3, 1, 2])
    results = list(result_iterator)

assert results == ["record-3", "record-1", "record-2"]
print(results)
```

sleep 在这里模拟阻塞 I/O，不代表实际网络速度。两名 worker 可以重叠等待，但结果仍按输入 3、1、2 排列。

map 返回的是结果迭代器。代码不消费它，就没有在这个位置把每个结果和异常领取出来。迭代到某个失败结果时，会抛出该任务异常。

4.2 想哪个先完成就先处理，用 as_completed

```python
# runnable: hb15_future_exceptions
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_number(text: str) -> int:
    return int(text)


successes = {}
failures = {}
with ThreadPoolExecutor(max_workers=3) as pool:
    pending = {
        pool.submit(parse_number, text): text
        for text in ["10", "bad", "20"]
    }
    for future in as_completed(pending):
        original = pending[future]
        try:
            successes[original] = future.result()
        except ValueError as exc:
            failures[original] = type(exc).__name__

assert successes == {"10": 10, "20": 20}
assert failures == {"bad": "ValueError"}
print(successes, failures)
```

submit 交回 Future，Future 代表那项工作的状态，不是计算结果。as_completed 依次给出已完成的 Future，再用 result 取成功值或重新抛出异常。

用字典保存 Future → 原输入，是为了失败时知道是哪条数据出了问题。任务完成先后不固定，因此断言内容，不断言这个字典的打印顺序。

不要只写 submit 后不再管。工作函数内部即使抛错，主线程也未必在你希望的位置自动报错，异常会保存在 Future 中等你领取。

4.3 cancel 能取消排队任务，不能强杀正在运行的线程

```python
# runnable: hb15_future_cancel
from concurrent.futures import ThreadPoolExecutor, CancelledError
from threading import Event


started = Event()
release = Event()


def first_job() -> str:
    started.set()
    if not release.wait(timeout=5):
        raise TimeoutError("release was not signaled")
    return "first"


with ThreadPoolExecutor(max_workers=1) as pool:
    first = pool.submit(first_job)
    try:
        assert started.wait(timeout=5)
        second = pool.submit(lambda: "second")
        assert first.cancel() is False
        assert second.cancel() is True
    finally:
        release.set()
    assert first.result(timeout=5) == "first"
    try:
        second.result()
    except CancelledError:
        cancelled = True
    else:
        cancelled = False
    assert cancelled
print("queued task cancelled; running task finished")
```

池只有一个 worker，first 已占住它，因此 second 还没开始，可以取消。first 已经运行，cancel 返回 False，只能让它自己检查停止信号或正常结束。

`future.result(timeout=...)` 超时表示调用方没在期限内等到结果，不代表工作线程被杀掉。线程池上下文退出时通常仍会等待运行中的任务，所以任务本身也需要合理的 I/O 超时和协作停止机制。

不要在容量很小的池中，让一个任务阻塞等待“提交到同一个池中的另一个任务”。如果所有 worker 都在等排队者，就可能死锁。

---

5）进程池：独立内存换来计算并行，也带来传输成本

5.1 Windows 为什么必须保护入口

Windows 常用 spawn 启动子进程：新的解释器导入主模块，准备执行工作函数。

如果模块一导入就创建进程池，子进程导入时又建池，就会重复启动，或在启动阶段报错。`if __name__ == "__main__":` 把真正启动动作限定到主入口。

工作函数放在模块顶层，方便子进程导入并找到它。不要把 lambda、局部函数或打开的数据库连接随手交给进程池，它们通常不满足这里的序列化要求。

5.2 一份完整的计算例子

```python
# runnable: hb15_process_pool
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp


def checksum(limit: int) -> int:
    return sum((number * number) % 97 for number in range(limit))


def main() -> None:
    inputs = [20_000, 30_000, 40_000]
    expected = [checksum(limit) for limit in inputs]
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=2, mp_context=context) as pool:
        results = list(pool.map(checksum, inputs))
    assert results == expected
    assert len(results) == 3
    print(results)


if __name__ == "__main__":
    mp.freeze_support()
    main()
```

父进程把三个整数参数交给池，工作进程分别计算，结果整数再传回父进程。`pool.map` 仍按输入顺序提供结果。

这里故意选较小数据，便于快速验证正确性，不声称进程池一定比串行快。进程启动、参数打包、进程通信和结果传输都需要时间，任务很小时开销可能占大头。

`freeze_support` 用于兼顾某些打包后的运行场景；普通解释器脚本里保留它无妨，但它不能代替 main 保护。

5.3 每个进程里的普通全局变量不是共享状态

线程共享同一进程内的对象；进程各有自己的普通内存空间。子进程改了一个全局列表，父进程的同名列表不会因为名字一样就跟着变。

不同启动方式在初始内存建立方式上有差别，但都不能据此把普通 Python 全局对象当成可随意互相修改的共享内存。本章显式使用 spawn，减少平台默认值造成的误会。

参数通常需要序列化。如果传入一个列表，子进程接到并修改的是传过去的数据，不是在远程操作父进程的那个列表对象。想拿到改动，应返回结果或设计明确 IPC。

5.4 multiprocessing.Pool：另一套常见进程池接口

你还会遇到 `multiprocessing.Pool(processes=2)`。它与 ProcessPoolExecutor 都能把任务分给工作进程，但方法和返回对象不是同一套。下面通过 spawn 上下文创建 Pool，相当于明确选择启动方式，不修改整个程序的全局默认值。

```python
# runnable: hb15_multiprocessing_pool
import multiprocessing as mp


def square(number: int) -> int:
    if number < 0:
        raise ValueError("number must be non-negative")
    return number * number


def main() -> None:
    context = mp.get_context("spawn")
    with context.Pool(processes=2) as pool:
        results = pool.map(square, [3, 1, 2], chunksize=1)
        assert results == [9, 1, 4]
        pending = pool.apply_async(square, (4,))
        assert pending.get(timeout=5) == 16
        failed = pool.apply_async(square, (-1,))
        try:
            failed.get(timeout=5)
        except ValueError:
            pass
        else:
            raise AssertionError("worker error was not propagated")
    print(results)


if __name__ == "__main__":
    mp.freeze_support()
    main()
```

`processes=2` 指两个工作进程，不是只能提交两条数据。`pool.map` 把每个数字交给 square，阻塞等待这一组结果，然后直接返回按输入顺序排列的列表。这里 chunksize=1 表示每份分发批次包含一项，适合观察小例子；真实大批数据需要结合任务规模选择批大小。

对照一下：ProcessPoolExecutor 使用 max_workers，submit 返回 Future，用 result 取结果；multiprocessing.Pool 使用 processes，apply_async 返回 AsyncResult，用 get 取结果。方法名中的 async 只是这个接口不在提交处等待结果，不是 asyncio 协程，也不能因此直接 await 它。

`(4,)` 是工作函数的位置参数元组，所以 square 收到整数 4，而不是收到一个元组。get 等到失败结果时，会在调用方重新抛出工作函数的异常；get 自己等待超时则是 multiprocessing.TimeoutError，也不会因此自动撤销那项任务。

Pool 的上下文退出会调用 terminate。这个例子在退出前已经通过 map/get 收完所有结果，不能照抄成“apply_async 后立刻离开 with”，再期待未完成任务全部自然跑完。如果手动管理生命周期，通常正常路径先 close 停止接收新任务，再 join 等已有任务退出；异常停止则明确 terminate，再 join 收尾。[Pool 生命周期与结果对象](https://docs.python.org/3.11/library/multiprocessing.html#module-multiprocessing.pool)

---

6）进程之间通过消息沟通，不靠猜全局变量

6.1 Queue 的完整发送、接收和收尾

```python
# runnable: hb15_process_queue
import multiprocessing as mp


def producer(queue, values: list[int]) -> None:
    for value in values:
        queue.put((value, value * value))
    queue.put(None)


def main() -> None:
    context = mp.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=producer, args=(queue, [2, 3, 4]))
    process.start()
    received = []
    try:
        while True:
            message = queue.get(timeout=5)
            if message is None:
                break
            received.append(message)
        process.join(timeout=5)
        assert not process.is_alive()
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        queue.close()
        queue.join_thread()
    assert received == [(2, 4), (3, 9), (4, 16)]
    print(received)


if __name__ == "__main__":
    mp.freeze_support()
    main()
```

工作进程先发送三个结果，最后发送 None，约定它表示“没有更多消息”。接收方遇到 None 停止接收。

这里先接收再 join，避免工作进程正在等队列缓冲数据被接收，父进程却只顾等它退出。真实代码不能靠 queue.empty 判断所有生产者已经结束，它可能与其他进程的动作竞态。

None 作为结束标记的前提是正常业务消息不会使用 None。若业务需要传 None，就改用不会混淆的消息结构，例如包含 kind 字段。

finally 里的 terminate 只是这个演示失败或卡住时的兜底，不是正常停止机制。强行终止可能中断清理、损坏队列或丢失未完成工作；正常路径应发送结束消息并等待自然退出。

6.2 哪种 IPC 适合哪种情况

Queue 适合多项消息传输；Pipe 可以表达两个端点的通信；Manager 提供代理式共享对象，但有额外通信开销；共享内存适合特定大数据场景，同时需要单独处理同步和生命周期。

Redis 属于另一层选择：多个进程甚至多台机器通过客户端访问外部 Redis 服务，用约定的数据结构保存状态或传递消息。它不是 Python 自带的“共享字典”，也不会在你导入 multiprocessing 后自动出现。

用 Redis 传人员记录时，通常把编号、姓名等字段编码成约定的字符串、字节或 JSON，接收方再解析；传过去的是数据表示，不是同一个 Python 对象引用。服务地址、认证、客户端依赖、超时、消息确认与重复处理等都需要另外配置和设计。本章不安装客户端、不连接 Redis，也不把外部服务当成运行例子的前提。

不要一开始就追求“让所有进程共享一个巨大字典”。先试着把任务设计成输入一份数据、返回一份结果，往往更容易测试和排错。

6.3 Pipe：先分清哪一端发送，哪一端接收

`Pipe()` 默认两端都能收发；`Pipe(duplex=False)` 创建单向管道，返回值顺序是接收端在前、发送端在后。用明确变量名，比靠记住 a、b 分别做什么更可靠。

```python
# runnable: hb15_one_way_pipe
import multiprocessing as mp


def send_summary(connection, values: list[int]) -> None:
    try:
        connection.send({"count": len(values), "total": sum(values)})
    finally:
        connection.close()


def main() -> None:
    context = mp.get_context("spawn")
    receive_end, send_end = context.Pipe(duplex=False)
    assert receive_end.readable and not receive_end.writable
    assert send_end.writable and not send_end.readable
    process = context.Process(target=send_summary, args=(send_end, [2, 3, 4]))
    started = False
    try:
        process.start()
        started = True
        send_end.close()
        if not receive_end.poll(5):
            raise TimeoutError("no summary arrived")
        summary = receive_end.recv()
        assert summary == {"count": 3, "total": 9}
        process.join(timeout=5)
        assert not process.is_alive()
        assert process.exitcode == 0
        try:
            receive_end.recv()
        except EOFError:
            pass
        else:
            raise AssertionError("expected EOF after the single message")
    finally:
        receive_end.close()
        send_end.close()
        if started:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if not process.is_alive():
                process.close()
    print(summary)


if __name__ == "__main__":
    mp.freeze_support()
    main()
```

主进程创建两端，把 send_end 作为参数交给工作进程。子进程用自己的发送端发送一条字典，随后关闭；主进程只使用接收端，收到的数据是反序列化后的独立对象，不是远程共享字典。

`process.start()` 成功之后，主进程立即关闭自己那份 send_end。子进程持有的发送端仍能工作；如果主进程一直留着自己的发送端，即使子进程退出，接收方也可能还以为“仍有发送者”，无法按预期看到 EOF。

poll(5) 给等待首条数据设置一个五秒边界，接下来仍要用 recv 真正取消息；连接意外关闭时，接收操作也可能失败，不能把“可以尝试读”当成“业务消息一定有效”。第一次 recv 得到消息后，本例先 join 确认发送进程已经退出，再直接 recv 验证 EOF。这样把“消息已收到”和“发送方已结束”分开，也不依赖不同平台对已关闭管道的 poll 表现完全一致。

send/recv 会序列化和反序列化 Python 对象，只应与可信的进程端点交换这类数据。发送巨大对象仍有复制与传输开销；多个执行者共用同一发送端还需要协调，不能把一个端点当成无限并发的消息队列。

示例正常路径先接收、再等进程退出，最后关闭本进程持有的端点与 Process 句柄。terminate 仅用于失败时停止本例创建的工作进程，不是正常完成通知。[Pipe 与 Connection](https://docs.python.org/3.11/library/multiprocessing.html#multiprocessing.Pipe)

6.4 进程任务异常也要收集

ProcessPoolExecutor 同样返回 Future，调用 result 时可收到工作任务异常。异常本身和参数、返回值一样，也涉及跨进程序列化，自定义异常和不可序列化状态需要特别注意。

进程突然退出可能导致进程池不可继续使用，不要把“某一条数据转换失败”和“整个 worker 意外崩溃”当成同一种情况。前者常能逐项记录，后者需要池级别恢复策略。

---

7）练习与完整参考答案

7.1 练习一：五个名额不能发出第六个

十个线程任务同时申请，成功返回 True，名额不足返回 False。最终恰好五次成功，剩余名额为 0。

```python
# runnable: hb15_exercise_quota
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class Quota:
    def __init__(self, remaining: int) -> None:
        self.remaining = remaining
        self.lock = Lock()

    def acquire(self) -> bool:
        with self.lock:
            if self.remaining == 0:
                return False
            self.remaining -= 1
            return True


quota = Quota(5)
with ThreadPoolExecutor(max_workers=10) as pool:
    futures = [pool.submit(quota.acquire) for _ in range(10)]
    results = [future.result(timeout=5) for future in futures]
assert sum(results) == 5
assert quota.remaining == 0
print(sum(results), quota.remaining)
```

答案把检查和减一放在同一把锁里。最终检查 remaining 时，所有任务已结束，因此这里没有与其他写入并发。

7.2 练习二：线程池逐项保存成功和失败

输入 `["1", "x", "3"]`，转换失败不能妨碍其他结果领取。输出应保留输入位置，而不是按完成先后乱排。

```python
# runnable: hb15_exercise_result_positions
from concurrent.futures import ThreadPoolExecutor, as_completed


inputs = ["1", "x", "3"]
results = [None] * len(inputs)
with ThreadPoolExecutor(max_workers=3) as pool:
    pending = {pool.submit(int, value): index for index, value in enumerate(inputs)}
    for future in as_completed(pending):
        index = pending[future]
        try:
            results[index] = ("ok", future.result())
        except ValueError:
            results[index] = ("error", inputs[index])
assert results == [("ok", 1), ("error", "x"), ("ok", 3)]
print(results)
```

Future → 下标解决了“可以按完成顺序处理，但仍按原位置存结果”。不要把 as_completed 的先后当成输入顺序。

7.3 练习三：在进程池中收集一个明确失败

工作函数计算非负整数平方，负数抛 ValueError。父进程记录成功值与失败输入。必须保留 Windows 入口保护。

```python
# runnable: hb15_exercise_process_errors
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp


def square(number: int) -> int:
    if number < 0:
        raise ValueError("number must be non-negative")
    return number * number


def main() -> None:
    successes = {}
    failures = []
    with ProcessPoolExecutor(
        max_workers=2, mp_context=mp.get_context("spawn")
    ) as pool:
        pending = {pool.submit(square, value): value for value in [2, -1, 3]}
        for future in as_completed(pending):
            value = pending[future]
            try:
                successes[value] = future.result()
            except ValueError:
                failures.append(value)
    assert successes == {2: 4, 3: 9}
    assert failures == [-1]
    print(successes, failures)


if __name__ == "__main__":
    mp.freeze_support()
    main()
```

这个例子捕获的是已知的输入 ValueError。不要宽泛捕获所有错误后都写成“数据有问题”，否则进程启动失败、池崩溃等基础设施错误也会被误记。

---

8）运行前后检查清单

启动前确认任务是不是足够大、池大小是不是有上限、所有工作函数是否可导入。运行中确认没有持锁做长等待、没有让同一个小池里的任务互等。

收尾时确认每个 Future 的结果或异常都被领取，线程和进程自然退出。超时只是某个等待范围的边界，不自动保证任务停止，更不代表下游写入被撤销。

性能测试请分开记录初始化耗时和稳定运行耗时，不要用这个快速正确性示例的耗时做“线程/进程谁永远更快”的结论。

官方参考：[threading](https://docs.python.org/3.11/library/threading.html)、[concurrent.futures](https://docs.python.org/3.11/library/concurrent.futures.html)、[multiprocessing](https://docs.python.org/3.11/library/multiprocessing.html)、[free-threaded CPython](https://docs.python.org/3/howto/free-threading-python.html)。

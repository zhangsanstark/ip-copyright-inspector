16 asyncio：把创建、调度、等待和收尾分开看

asyncio 不是给函数加上 async 就自动变快。它真正擅长的是：一项工作在等待 I/O 时，让同一事件循环继续推进其他已就绪工作。要读懂代码，必须知道哪份工作只是被创建了，哪份已经交给事件循环，谁正在等谁。

阅读路线：1 协程对象 → 2 Task 与 await → 3 gather → 4 TaskGroup → 5 取消与超时 → 6 并发上限 → 7 阻塞调用 → 8 练习及答案。

以 Python 3.11 的标准 asyncio 行为为基线。代码只用本地事件和标准库模拟等待，不请求外部服务。运行 `python scripts/check_handbook_examples.py --chapter 16 --show-output`。

---

1）调用 async 函数，先得到一份待执行的协程

1.1 普通调用与异步调用的差别

普通函数 `result = add(1, 2)` 在这句话里执行函数体，完成后把结果交给 result。

协程函数 `coro = job()` 则先创建协程对象。这时函数体不会因为“已经加了括号”就完整运行，必须被等待或调度，执行才会推进。

```python
# runnable: hb16_coroutine_creation
import asyncio
import inspect


async def main() -> None:
    events = []

    async def job(name: str) -> str:
        events.append(f"{name} start")
        await asyncio.sleep(0)
        events.append(f"{name} end")
        return name.upper()

    coroutine = job("a")
    assert inspect.iscoroutine(coroutine)
    assert events == []
    events.append("created")
    first = await coroutine
    second = await job("b")
    assert (first, second) == ("A", "B")
    assert events == ["created", "a start", "a end", "b start", "b end"]
    print(events)


asyncio.run(main())
```

`coroutine = job("a")` 后 events 仍为空，这是“创建并不等于执行”的直接证据。

`await coroutine` 开始推进 a。a 在 sleep(0) 处交回控制权，但此时 b 还没创建，更没被调度，所以不存在“趁 a 等待运行 b”的可能。

a 完成后，main 才走到 `await job("b")`。两行都用了 await，实际仍是 a 完成后才开始 b。

1.2 await 暂停的是当前任务，不是把整个线程睡死

await 只能用于可等待对象，例如协程、Task、Future。它表示“这一步需要结果，结果没准备好时，当前任务先等一下”。

能否让出执行机会，还取决于等待对象是否已经完成。不是每出现一个 await 都必然切走；等待一个已经完成的结果可能马上继续。

`asyncio.sleep(0)` 明确提供一次让其他就绪任务运行的机会，但它不是跨业务任务的严格排序工具。需要确定依赖顺序时，用 Event、Queue 等表达条件。

1.3 asyncio.run 是程序入口，不是每个方法都套一层

普通脚本用 `asyncio.run(main())` 创建并管理事件循环，运行 main，最后收尾。已在事件循环里时，通常直接 await，不要再次调用 asyncio.run。

交互式环境有时已提供顶层 await。脚本与交互环境的入口方式不同，不代表协程函数内部规则不同。

---

2）Task 是事件循环已经接手管理的工作

2.1 三个概念放在一张表里

| 写法 | 做了什么 | 此时你拿到什么 |
| :-- | :-- | :-- |
| `job()` | 创建协程对象 | 待推进的协程 |
| `asyncio.create_task(job())` | 把协程交给事件循环管理 | Task，保存执行状态和最终结果 |
| `await task` | 当前任务等它完成 | 成功结果，或抛出的异常/取消 |

在本章基线下，create_task 把工作排入调度，不表示下一句之前它必然已经执行完。要知道某个具体阶段完成了，应等待明确通知，而不是看代码行距猜。

2.2 两项任务都先调度，才有重叠推进的机会

```python
# runnable: hb16_task_order
import asyncio


async def main() -> None:
    a_started = asyncio.Event()
    b_finished = asyncio.Event()
    events = []

    async def job_a() -> str:
        events.append("A start")
        a_started.set()
        await b_finished.wait()
        events.append("A end")
        return "A result"

    async def job_b() -> str:
        await a_started.wait()
        events.append("B start")
        events.append("B end")
        b_finished.set()
        return "B result"

    first = asyncio.create_task(job_a())
    second = asyncio.create_task(job_b())
    results = await asyncio.gather(first, second)
    assert results == ["A result", "B result"]
    assert events == ["A start", "B start", "B end", "A end"]
    assert first.done() and second.done()
    assert first.result() == "A result"
    print(events)
    print(results)


asyncio.run(main())
```

A 开始后通知 a_started，然后等待 b_finished。B 必须先收到 a_started，才能继续；B 做完后通知 b_finished，A 才能返回。

因此 B 先完成是依赖关系保证的，不是用一个较短的 sleep 赌 B 更快。最后结果仍按 gather 的输入顺序排列，所以 A 的结果在前。

2.3 Task 的状态怎样读

`task.done()` 表示已经结束，结束原因可能是成功、失败或取消。done 为真，不等于业务成功。

`task.result()` 在成功完成时返回值，失败时重新抛异常，取消时抛 CancelledError。任务还没结束时调用 result，会抛 InvalidStateError；它不会像 await 那样自动等待。

保存 Task 引用，并在明确位置 await 或交给 TaskGroup 管理。随手创建后台 Task 后不再管，可能让异常无人领取、停机时也不清楚该等谁。

同一个协程对象不能在耗尽后再次当作新任务运行。想重新执行，应再次调用协程函数创建新对象。已完成的 Task 则可以再次 await 领取同一结果，这两者不要混淆。

---

3）gather：一起等结果，但不是自动回滚的一组操作

3.1 它按输入位置收集，不按完成时间排列

gather 接收协程时，会把它们调度成任务；接收已创建的 Task 时，继续等待那些任务。返回结果列表与参数一一对应。

因此可以用 gather 同时查三份独立信息，最后仍知道第一个位置是哪份数据。不要根据“日志先打印了谁”去调整结果下标。

3.2 默认有一个失败，其他任务不会因此自动取消

```python
# runnable: hb16_gather_failure
import asyncio


async def main() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    events = []

    async def slow() -> str:
        started.set()
        await release.wait()
        events.append("slow finished")
        return "ok"

    async def broken() -> None:
        await started.wait()
        raise ValueError("bad input")

    slow_task = asyncio.create_task(slow())
    try:
        await asyncio.gather(slow_task, broken())
    except ValueError:
        events.append("caught error")
    else:
        raise AssertionError("expected error was not propagated")
    assert not slow_task.done()
    assert not slow_task.cancelled()
    release.set()
    assert await slow_task == "ok"
    assert events == ["caught error", "slow finished"]
    print(events)


asyncio.run(main())
```

broken 抛错后，main 收到 ValueError，离开 gather。slow 仍在等 release，没有自动取消。main 发通知后，它继续完成，最后明确 await 收走结果。

如果在 except 后直接结束 main，可能看到剩余任务被取消。那是 asyncio.run 退出时的清理，不是 gather 因为某个兄弟任务失败而自动取消其他任务。

取消 gather 本身时，尚未完成的子任务会受到取消请求；但 gather 已因异常完成后，再对这个已完成对象 cancel，不能指望它追溯取消仍运行的兄弟任务。

3.3 return_exceptions=True 需要逐项检查

```python
# runnable: hb16_gather_collect_errors
import asyncio


async def parse(text: str) -> int:
    await asyncio.sleep(0)
    return int(text)


async def main() -> None:
    results = await asyncio.gather(
        parse("10"), parse("bad"), parse("20"), return_exceptions=True
    )
    assert results[0] == 10
    assert isinstance(results[1], ValueError)
    assert results[2] == 20
    successes = [value for value in results if not isinstance(value, BaseException)]
    failures = [type(value).__name__ for value in results if isinstance(value, BaseException)]
    assert successes == [10, 20]
    assert failures == ["ValueError"]
    print(successes, failures)


asyncio.run(main())
```

这个选项把异常对象放到对应位置，不是修好了异常。后续若直接对 results 求和或作为正常字符串返回，仍会出错。

检查 BaseException 是为了涵盖取消等不是普通 Exception 子类的情况。真正业务中通常应转换成明确的成功/失败记录，而不是让裸异常对象一路流进响应数据。

---

4）TaskGroup：共同开始，也共同收尾

4.1 正常退出代码块，说明组内任务已结束

```python
# runnable: hb16_taskgroup_success
import asyncio


async def load(name: str) -> str:
    await asyncio.sleep(0)
    return name.upper()


async def main() -> None:
    async with asyncio.TaskGroup() as group:
        users = group.create_task(load("users"))
        orders = group.create_task(load("orders"))
    assert users.done() and orders.done()
    assert users.result() == "USERS"
    assert orders.result() == "ORDERS"
    print(users.result(), orders.result())


asyncio.run(main())
```

`group.create_task` 安排执行；退出 async with 时统一等待。正常走到代码块后面，才读取成功结果。

这里说“正常退出”很重要：如果有任务失败，控制流会进入异常处理，不是保证所有变量都能读取成功结果。

4.2 一个非取消异常失败，通常会请求取消其他任务

```python
# runnable: hb16_taskgroup_failure
import asyncio


async def main() -> None:
    started = asyncio.Event()
    never_released = asyncio.Event()
    events = []
    caught = []

    async def slow() -> None:
        try:
            started.set()
            await never_released.wait()
        finally:
            events.append("slow cleaned")

    async def broken() -> None:
        await started.wait()
        raise ValueError("broken")

    try:
        async with asyncio.TaskGroup() as group:
            slow_task = group.create_task(slow())
            group.create_task(broken())
    except* ValueError as errors:
        caught.extend(errors.exceptions)
        events.append("group failed")
    assert len(caught) == 1
    assert slow_task.cancelled()
    assert events == ["slow cleaned", "group failed"]
    print(events)


asyncio.run(main())
```

broken 失败 → 任务组请求取消 slow → slow 在等待处收到取消 → 执行 finally → 任务组等它收尾 → 外层收到异常组。

`except* ValueError` 处理异常组中相应的异常，而不是把异常组误当一个普通 ValueError。可能有多个任务在取消到达前已经失败，因此组里不一定只有一项。

单个任务的 CancelledError 不等于普通业务失败触发的整组失败；KeyboardInterrupt、SystemExit 也有特殊处理。这里展示的是常见的 ValueError 路径，不把所有 BaseException 都说成同一种规则。

4.3 任务组不是数据库事务

取消只要求未完成任务停止继续推进。某个任务已经发出的请求、已经提交的数据库写入，不会因为旁边任务失败就自动撤销。

需要“要么全部成功，要么补偿”的业务时，还要设计事务范围、幂等键、补偿动作或状态机。TaskGroup 解决任务生命周期，不替代这些业务机制。

---

5）取消与超时：发出停止请求以后，还要等清理

5.1 cancel 不等于瞬间消失

```python
# runnable: hb16_cancel_cleanup
import asyncio


async def main() -> None:
    started = asyncio.Event()
    events = []

    async def worker() -> None:
        try:
            started.set()
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            events.append("cancel received")
            raise
        finally:
            events.append("cleaned")

    task = asyncio.create_task(worker())
    await started.wait()
    assert task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        events.append("caller knows")
    assert task.cancelled()
    assert events == ["cancel received", "cleaned", "caller knows"]
    print(events)


asyncio.run(main())
```

cancel 请求取消，协程通常在可中断的等待位置收到 CancelledError。外层继续 await，是为了确认它经过收尾并领取最终取消状态。

捕获 CancelledError 后再 raise，把取消继续传给上层。若悄悄吞掉并返回正常结果，上层就可能误认为操作成功，TaskGroup、timeout 等也可能无法按预期协调。

本章基线中，CancelledError 继承 BaseException，不属于普通 Exception。普通 `except Exception` 不会把它抓走，裸 except、`except BaseException` 或专门捕获后不再抛出才是常见问题。

5.2 timeout 给的是等待范围，不是强制中止按钮

```python
# runnable: hb16_timeout
import asyncio


async def main() -> None:
    events = []
    try:
        async with asyncio.timeout(0.01):
            try:
                events.append("waiting")
                await asyncio.Event().wait()
            finally:
                events.append("cleaned")
    except TimeoutError:
        events.append("timed out")
    assert events == ["waiting", "cleaned", "timed out"]
    print(events)


asyncio.run(main())
```

没有任何人 set 这个 Event，所以它不会正常完成。达到期限后，timeout 通过取消当前任务的等待来打断；内部 finally 先执行，退出上下文后再以 TimeoutError 交给外层。

因此捕获 TimeoutError 放在 async with 外面。不要以为事件在 0.01 秒后“自动成功”，也不要断言程序总耗时必须精确等于 0.01 秒。

如果协程里正在跑长时间同步代码，事件循环无法及时处理超时。即使正常触发取消，清理也可能需要时间；超时不保证函数恰好在期限那一刻返回。

5.3 锁与资源也要跟着收尾

用 `async with` 管理异步锁、连接等资源，或者在 try/finally 中释放。不要在 finally 里直接掩盖原始异常，也不要把取消当成“无需清理”。

asyncio.Lock 只适合协调同一事件循环中的协程，不是跨线程或跨进程的锁。也不要拿 threading.Lock 后跨 await 等其他协程，否则可能把事件循环线程阻塞住。

---

6）Semaphore 限制活跃数量，Queue 限制积压

6.1 任务可以很多，同时占用资源的只能几个

```python
# runnable: hb16_semaphore
import asyncio


async def main() -> None:
    gate = asyncio.Semaphore(2)
    active = 0
    maximum = 0

    async def work(number: int) -> int:
        nonlocal active, maximum
        async with gate:
            active += 1
            maximum = max(maximum, active)
            try:
                await asyncio.sleep(0)
                return number * 10
            finally:
                active -= 1

    results = await asyncio.gather(*(work(number) for number in range(5)))
    assert results == [0, 10, 20, 30, 40]
    assert maximum == 2
    assert active == 0
    print(results, maximum)


asyncio.run(main())
```

两张通行证让最多两项任务进入保护范围。它们在 sleep 处等待时仍占着通行证，因为这段 I/O 尚未完成；其他任务继续等 gate。

active 的加减之间没有额外 await，在这个单事件循环示例里不会被另一个协程插入到加减操作中间。若把共享状态交给线程，或把一个业务检查拆开并加入 await，就要重新分析同步。

maximum 表示同时处于这段未完成操作的数量，不是两个协程同时在两个 CPU 核心执行 Python 代码。

6.2 Semaphore 不减少已经创建的 Task 数量

如果一次创建一百万 Task，再让它们等 gate，内存里仍然有一百万份任务对象。并发入口被限制，不等于积压数量被限制。

有界 Queue 可以让生产者在队列满时 await put，暂缓继续生产。固定数量 worker 从队列取任务，避免为每条数据都创建一个常驻 Task。

```python
# runnable: hb16_bounded_queue
import asyncio


async def main() -> None:
    queue = asyncio.Queue(maxsize=2)
    stop = object()
    results = []

    async def worker() -> None:
        while True:
            item = await queue.get()
            try:
                if item is stop:
                    return
                await asyncio.sleep(0)
                results.append(item * item)
            finally:
                queue.task_done()

    async with asyncio.TaskGroup() as group:
        for _ in range(2):
            group.create_task(worker())
        for number in range(6):
            await queue.put(number)
        for _ in range(2):
            await queue.put(stop)
        await queue.join()
    assert sorted(results) == [0, 1, 4, 9, 16, 25]
    assert queue.empty()
    print(sorted(results))


asyncio.run(main())
```

只有两个 worker Task；队列最多积压两个尚未取出的项目。此外每个 worker 可能正在处理一项，因此“队列上限 2”不表示系统里总共只有两项工作。

每次 get 都对应一次 task_done，包括结束标记。join 等待未完成计数归零，不负责自动停止 worker，所以还需要结束标记。

每名 worker 都要收到一个标记才能退出。这里只测试正常处理；如果 worker 抛错，TaskGroup 会协调失败收尾，不能把 queue.join 永远等待当成错误处理方案。

---

7）async 函数里的阻塞调用，仍会挡住事件循环

7.1 为什么 time.sleep 不适合直接放在协程里

`time.sleep(1)` 让当前线程暂停。事件循环就在这个线程上，所以其他协程也没法继续。

`await asyncio.sleep(1)` 则登记一个等待，交回事件循环；其他就绪任务仍可推进。

同步数据库驱动、同步 HTTP 客户端、长时间文件操作也可能阻塞。判断一个函数是否适合直接放进 async 代码，不是看它的函数名，而是看它是否用可协作的等待方式。

7.2 旧的阻塞 I/O 可以用 to_thread 过渡

```python
# runnable: hb16_to_thread_bridge
import asyncio
from threading import Event


async def main() -> None:
    started = Event()
    release = Event()
    events = []

    def blocking_read() -> str:
        started.set()
        if not release.wait(timeout=5):
            raise TimeoutError("thread was not released")
        return "data"

    task = asyncio.create_task(asyncio.to_thread(blocking_read))
    try:
        async with asyncio.timeout(3):
            while not started.is_set():
                await asyncio.sleep(0)
            events.append("event loop still running")
            assert not task.done()
    finally:
        release.set()
    assert await task == "data"
    assert events == ["event loop still running"]
    print(events)


asyncio.run(main())
```

阻塞函数在线程里等 release，事件循环仍能执行 main 的检查和后续语句。最后由 main 发出释放通知，再 await 领取结果。

这里 Event 来自 threading，因为一端在线程、一端在事件循环线程，不能把 asyncio.Event 直接当线程同步工具。

to_thread 主要用于阻塞 I/O 过渡。默认 GIL 下，纯 Python 重计算放进线程不等于获得多核并行；同时还可能争抢 CPU 影响事件循环响应。

取消等待 to_thread 的协程也不会把已经运行的线程函数强杀。真实阻塞函数仍应设置自己的超时，必要时支持停止信号。

---

8）练习与完整参考答案

8.1 练习一：按输入顺序保留成功与失败

并发转换三个字符串，结果写成 `("ok", value)` 或 `("error", original)`。不要把异常直接当作正常值返回。

```python
# runnable: hb16_exercise_parse
import asyncio


async def parse_one(text: str):
    await asyncio.sleep(0)
    try:
        return ("ok", int(text))
    except ValueError:
        return ("error", text)


async def main() -> None:
    results = await asyncio.gather(*(parse_one(text) for text in ["1", "x", "3"]))
    assert results == [("ok", 1), ("error", "x"), ("ok", 3)]
    print(results)


asyncio.run(main())
```

这里只捕获已知的 ValueError，不会把任务取消转换成普通业务失败。输入类型等其他错误仍能向上暴露。

8.2 练习二：最多两项，每项都有超时

输入 0、1、2、3，只有 2 故意一直等待，应该得到 timeout。超时从取得通行证后开始计算，而不是把排队时间也算进去。

```python
# runnable: hb16_exercise_limited_timeout
import asyncio


async def main() -> None:
    gate = asyncio.Semaphore(2)

    async def run_one(number: int):
        async with gate:
            try:
                async with asyncio.timeout(0.02):
                    if number == 2:
                        await asyncio.Event().wait()
                    else:
                        await asyncio.sleep(0)
                    return (number, "ok")
            except TimeoutError:
                return (number, "timeout")

    results = await asyncio.gather(*(run_one(number) for number in range(4)))
    assert results == [(0, "ok"), (1, "ok"), (2, "timeout"), (3, "ok")]
    print(results)


asyncio.run(main())
```

如果要求“从提交起最多等这么久”，就应把 timeout 放在 gate 外面，让排队也处于计时范围。这不是哪种写法更高级，而是两个不同的服务约定。

8.3 练习三：取消后一定完成清理

任务开始后通知调用方；调用方取消任务并等待，最后确认资源列表为空，任务处于 cancelled 状态。

```python
# runnable: hb16_exercise_cancel_resource
import asyncio


async def main() -> None:
    resources = []
    started = asyncio.Event()

    async def hold_resource() -> None:
        resources.append("connection")
        try:
            started.set()
            await asyncio.Event().wait()
        finally:
            resources.remove("connection")

    task = asyncio.create_task(hold_resource())
    await started.wait()
    assert resources == ["connection"]
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert task.cancelled()
    assert resources == []
    print("resource released")


asyncio.run(main())
```

列表只是用来观察资源占用状态，不是真的数据库连接。重点是“先开始、收到取消、finally 清理、调用方等待收尾”的完整链条。

---

9）回看与资料

排错时按四个问题找：协程有没有被调度；是否把阻塞函数放进事件循环；异常有没有被 await 领取；失败或取消后还有谁没收尾。

不要用“单线程能撑十万连接”代替容量设计。连接池、文件描述符、内存、下游配额、任务积压、请求超时共同决定服务能承受多少工作。

官方参考：[协程与任务、gather、TaskGroup、timeout](https://docs.python.org/3.11/library/asyncio-task.html)、[异步同步原语](https://docs.python.org/3.11/library/asyncio-sync.html)、[异步队列](https://docs.python.org/3.11/library/asyncio-queue.html)、[asyncio 开发注意事项](https://docs.python.org/3.11/library/asyncio-dev.html)。

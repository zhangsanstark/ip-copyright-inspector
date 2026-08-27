"""线程、进程与 asyncio 的可运行并发实验。

运行方式：python examples/concurrency_lab.py
仅使用 Python 3.11+ 标准库，不访问网络，不写文件。
"""

from __future__ import annotations

import asyncio
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from threading import Lock


def simulated_blocking_io(job_id: int) -> str:
    time.sleep(0.05)
    return f"io-{job_id}"


class ProtectedCounter:
    """用线程锁保护完整的读改写过程。"""

    def __init__(self) -> None:
        self._value = 0
        self._lock = Lock()

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def increment(self) -> None:
        with self._lock:
            next_value = self._value + 1
            self._value = next_value


def increment_many(counter: ProtectedCounter, times: int) -> None:
    for _ in range(times):
        counter.increment()


def run_thread_demo() -> None:
    print("thread pool")

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(simulated_blocking_io, range(4)))

    assert results == ["io-0", "io-1", "io-2", "io-3"]
    print(f"thread results: {results}")

    counter = ProtectedCounter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(increment_many, counter, 1_000) for _ in range(4)]
        for future in futures:
            future.result()

    assert counter.value == 4_000
    print(f"protected counter: {counter.value}")


def cpu_checksum(limit: int) -> int:
    """模块顶层纯 Python 函数，可以被 Windows 子进程导入和 pickle。"""

    checksum = 0
    for number in range(limit):
        checksum += (number * number) % 97
    return checksum


def run_process_demo() -> None:
    print("process pool")

    limits = [970_000, 1_164_000]
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(cpu_checksum, limits))

    assert results == [46_560_000, 55_872_000]
    print(f"process checksums: {results}")


class AsyncConcurrencyProbe:
    """记录异步任务同时进入受限区的最大数量。"""

    def __init__(self) -> None:
        self.active = 0
        self.maximum_active = 0
        self._lock = asyncio.Lock()

    async def enter(self) -> None:
        async with self._lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)

    async def leave(self) -> None:
        async with self._lock:
            self.active -= 1


async def simulated_async_io(
    job_id: int,
    gate: asyncio.Semaphore,
    probe: AsyncConcurrencyProbe,
) -> str:
    async with gate:
        await probe.enter()
        try:
            await asyncio.sleep(0.03)
            return f"async-{job_id}"
        finally:
            await probe.leave()


def blocking_status() -> str:
    time.sleep(0.02)
    return "blocking-ok"


async def timeout_example() -> str:
    try:
        async with asyncio.timeout(0.02):
            await asyncio.sleep(0.20)
    except TimeoutError:
        return "timed out"
    return "unexpectedly completed"


async def run_async_demo() -> None:
    print("asyncio")

    gate = asyncio.Semaphore(2)
    probe = AsyncConcurrencyProbe()
    results = await asyncio.gather(
        *(simulated_async_io(job_id, gate, probe) for job_id in range(4))
    )

    assert results == ["async-0", "async-1", "async-2", "async-3"]
    assert probe.active == 0
    assert probe.maximum_active == 2
    print(f"gather results: {results}")
    print(f"maximum active async jobs: {probe.maximum_active}")

    bridge_result = await asyncio.to_thread(blocking_status)
    assert bridge_result == "blocking-ok"
    print(f"blocking bridge result: {bridge_result}")

    timeout_result = await timeout_example()
    assert timeout_result == "timed out"
    print(f"timeout handled: {timeout_result}")


def main() -> None:
    run_thread_demo()
    print()
    run_process_demo()
    print()
    asyncio.run(run_async_demo())
    print()
    print("all concurrency assertions passed")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

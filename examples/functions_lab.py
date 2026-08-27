"""Python 3.11+ 函数与 Pythonic 进阶练习。

运行方式：
    python examples/functions_lab.py

脚本只使用标准库。每组实验都有断言，适合修改后反复运行。
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from functools import cache, reduce, wraps
import inspect
import time
from typing import Any, get_type_hints, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
U = TypeVar("U")

request_count = 0


def section(title: str) -> None:
    """Print a small section marker."""
    print(f"\n[{title}]")


def min_max(values: list[int]) -> tuple[int, int]:
    """Return the smallest and largest values."""
    return min(values), max(values)


def log_only(message: str) -> None:
    """Print a message and return None implicitly."""
    print(message)


def demo_returns() -> None:
    section("返回值和拆包")

    result = min_max([3, 1, 8])
    smallest, largest = result
    print("原始元组:", result)
    print("拆包:", smallest, largest)

    return_value = log_only("只打印，不显式 return")
    print("默认返回值:", return_value)

    assert result == (1, 8)
    assert smallest == 1
    assert largest == 8
    assert return_value is None


def create_user(
    name: str,
    age: int = 18,
    active: bool = True,
) -> dict[str, object]:
    """Build a small user mapping."""
    return {"name": name, "age": age, "active": active}


def total(*numbers: float) -> float:
    """Add any number of positional values."""
    return sum(numbers)


def build_profile(name: str, **attributes: object) -> dict[str, object]:
    """Merge a required name with arbitrary keyword attributes."""
    return {"name": name, **attributes}


def request(
    path: str,
    /,
    method: str = "GET",
    *,
    timeout: float = 3.0,
) -> str:
    """Demonstrate positional-only and keyword-only parameters."""
    return f"{method} {path}, timeout={timeout:.1f}"


def demo_parameters() -> None:
    section("参数绑定")

    positional = create_user("Ada", 30, False)
    keywords = create_user("Lin", active=False, age=25)
    defaults = create_user("Bob")
    print("位置参数:", positional)
    print("关键字参数:", keywords)
    print("默认参数:", defaults)

    assert positional == {"name": "Ada", "age": 30, "active": False}
    assert keywords == {"name": "Lin", "age": 25, "active": False}
    assert defaults == {"name": "Bob", "age": 18, "active": True}

    values = [1, 2, 3.5]
    print("*args 收集与拆包:", total(*values))
    assert total(*values) == 6.5

    options = {"city": "London", "admin": True}
    profile = build_profile("Ada", **options)
    print("**kwargs 收集与拆包:", profile)
    assert profile == {"name": "Ada", "city": "London", "admin": True}

    line = request("/users", method="POST", timeout=5)
    print("仅限位置和仅限关键字:", line)
    assert line == "POST /users, timeout=5.0"

    try:
        request(path="/users")  # type: ignore[call-arg]
    except TypeError:
        print("path 只能按位置传入")
    else:
        raise AssertionError("positional-only argument should reject a keyword")

    try:
        request("/users", "GET", 5)  # type: ignore[misc]
    except TypeError:
        print("timeout 只能按关键字传入")
    else:
        raise AssertionError("keyword-only argument should reject a position")


def mutate(items: list[str]) -> None:
    """Mutate the shared list object."""
    items.append("new")


def rebind(items: list[str]) -> None:
    """Rebind only the local parameter name."""
    items = ["replacement"]
    assert items == ["replacement"]


def demo_object_sharing() -> None:
    section("参数指向对象")

    values = ["old"]
    mutate(values)
    print("原地修改后调用方可见:", values)
    assert values == ["old", "new"]

    rebind(values)
    print("函数内重新绑定后调用方不变:", values)
    assert values == ["old", "new"]


def append_bad(value: int, bucket: list[int] = []) -> list[int]:
    """Intentionally demonstrate the mutable default argument trap."""
    bucket.append(value)
    return bucket


def append_good(
    value: int,
    bucket: list[int] | None = None,
) -> list[int]:
    """Create a fresh list only when the caller omitted one."""
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket


def demo_mutable_defaults() -> None:
    section("可变默认参数")

    first_bad = append_bad(1)
    second_bad = append_bad(2)
    print("错误版本第一次:", first_bad)
    print("错误版本第二次:", second_bad)

    assert first_bad is second_bad
    assert second_bad == [1, 2]

    first_good = append_good(1)
    second_good = append_good(2)
    print("正确版本:", first_good, second_good)

    assert first_good == [1]
    assert second_good == [2]
    assert first_good is not second_good

    caller_list: list[int] = []
    returned = append_good(3, caller_list)
    print("显式传入空列表仍会修改它:", caller_list)
    assert caller_list == [3]
    assert returned is caller_list


def annotated_repeat(text: str, times: int) -> str:
    """Return repeated text; annotations are not runtime validation."""
    return text * times


def demo_type_hints() -> None:
    section("类型提示")

    print("正常调用:", annotated_repeat("py", 2))
    resolved_hints = get_type_hints(annotated_repeat)
    print("解析后的函数注解:", resolved_hints)

    surprising = annotated_repeat(3, 2)  # type: ignore[arg-type]
    print("运行时没有自动拦截错误类型:", surprising)

    assert annotated_repeat("py", 2) == "pypy"
    assert surprising == 6
    assert resolved_hints["text"] is str


def record_request() -> int:
    """Rebind a module-level counter with global."""
    global request_count
    request_count += 1
    return request_count


def make_counter(start: int = 0) -> Callable[[int], int]:
    """Build a stateful closure with an independent count."""
    count = start

    def increment(step: int = 1) -> int:
        nonlocal count
        count += step
        return count

    return increment


def demo_scope_and_closures() -> None:
    section("作用域、global、nonlocal 和闭包")

    before = request_count
    after = record_request()
    print("global 计数:", before, "->", after)
    assert after == before + 1

    first = make_counter(10)
    second = make_counter()
    outputs = [first(), first(5), second(), first()]
    print("两个闭包各自保存状态:", outputs)
    assert outputs == [11, 16, 1, 17]

    if True:
        block_value = "if 不创建普通块级作用域"
    print(block_value)
    assert block_value.startswith("if")

    outer_value = "outside"
    values = [outer_value for outer_value in range(3)]
    print("推导式结果:", values)
    print("外层变量仍然是:", outer_value)
    assert values == [0, 1, 2]
    assert outer_value == "outside"


def factorial(number: int) -> int:
    """Calculate a factorial recursively."""
    if number < 0:
        raise ValueError("number must be non-negative")
    if number <= 1:
        return 1
    return number * factorial(number - 1)


def flatten_recursive(values: list[Any]) -> list[Any]:
    """Flatten arbitrarily nested lists with recursion."""
    result: list[Any] = []
    for value in values:
        if isinstance(value, list):
            result.extend(flatten_recursive(value))
        else:
            result.append(value)
    return result


def demo_recursion() -> None:
    section("递归")

    print("5!:", factorial(5))
    nested = [1, [2, [3]], 4]
    flat = flatten_recursive(nested)
    print("递归扁平化:", flat)

    assert factorial(0) == 1
    assert factorial(5) == 120
    assert flat == [1, 2, 3, 4]

    try:
        factorial(-1)
    except ValueError as exc:
        print("非法输入:", exc)
    else:
        raise AssertionError("negative factorial should fail")


def demo_lambda_and_higher_order_functions() -> None:
    section("lambda 和高阶函数")

    orders = [
        {"id": 1, "amount": 100, "created_at": 3},
        {"id": 2, "amount": 200, "created_at": 2},
        {"id": 3, "amount": 200, "created_at": 1},
    ]
    orders.sort(key=lambda order: (-order["amount"], order["created_at"]))
    order_ids = [order["id"] for order in orders]
    print("金额降序、时间升序:", order_ids)
    assert order_ids == [3, 2, 1]

    larger = lambda left, right: left if left > right else right
    print("lambda 三元表达式:", larger(10, 20))
    assert larger(10, 20) == 20

    numbers = [1, 2, 3, 4]
    mapped = list(map(lambda number: number * number, numbers))
    filtered = list(filter(lambda number: number % 2 == 0, numbers))
    product = reduce(lambda left, right: left * right, numbers, 1)

    print("map:", mapped)
    print("filter:", filtered)
    print("reduce:", product)

    assert mapped == [1, 4, 9, 16]
    assert filtered == [2, 4]
    assert product == 24

    comprehension = [number * number for number in numbers]
    assert comprehension == mapped


def demo_late_binding() -> None:
    section("幽灵闭包，也叫晚期绑定")

    bad_functions = [lambda value: value + index for index in range(3)]
    bad_result = [function(10) for function in bad_functions]
    print("错误版本:", bad_result)
    assert bad_result == [12, 12, 12]

    good_functions = [
        lambda value, index=index: value + index
        for index in range(3)
    ]
    good_result = [function(10) for function in good_functions]
    print("默认参数锁住当前值:", good_result)
    assert good_result == [10, 11, 12]


def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """Log calls while preserving signature metadata and return values."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def repeat(times: int) -> Callable[[Callable[P, R]], Callable[P, list[R]]]:
    """Return a decorator that collects repeated call results."""
    if times < 1:
        raise ValueError("times must be positive")

    def decorate(func: Callable[P, R]) -> Callable[P, list[R]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[R]:
            return [func(*args, **kwargs) for _ in range(times)]

        return wrapper

    return decorate


def require_role(
    role: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Require a role in the first positional user's role set."""
    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not args:
                raise TypeError("the first positional argument must be a user")

            user = args[0]
            if not isinstance(user, dict):
                raise TypeError("user must be a dictionary")

            roles = user.get("roles", set())
            if role not in roles:
                raise PermissionError(f"missing role: {role}")

            return func(*args, **kwargs)

        return wrapper

    return decorate


@log_call
def add(left: int, right: int) -> int:
    """Add two integers."""
    return left + right


@repeat(times=3)
def greet(name: str) -> str:
    """Return one greeting."""
    return f"hello, {name}"


@require_role("admin")
def delete_user(operator: dict[str, Any], user_id: int) -> str:
    """Pretend to delete one user."""
    return f"deleted {user_id}"


def demo_decorators() -> None:
    section("装饰器")

    result = add(2, 3)
    print("透明返回:", result)
    print("保留函数名:", add.__name__)
    print("保留文档:", add.__doc__)

    assert result == 5
    assert add.__name__ == "add"
    assert add.__doc__ == "Add two integers."
    assert list(inspect.signature(add).parameters) == ["left", "right"]

    repeated = greet("Ada")
    print("带参数装饰器:", repeated)
    assert repeated == ["hello, Ada"] * 3
    assert greet.__name__ == "greet"

    admin = {"name": "root", "roles": {"admin", "reader"}}
    ordinary = {"name": "guest", "roles": {"reader"}}

    print("管理员调用:", delete_user(admin, 42))
    assert delete_user(admin, 42) == "deleted 42"

    try:
        delete_user(ordinary, 42)
    except PermissionError as exc:
        print("普通用户被拦截:", exc)
    else:
        raise AssertionError("missing admin role should fail")


def mark(name: str, events: list[str]):
    """Build a decorator that records entry and exit order."""
    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            events.append(f"enter {name}")
            try:
                return func(*args, **kwargs)
            finally:
                events.append(f"exit {name}")

        return wrapper

    return decorate


def demo_decorator_order() -> None:
    section("多个装饰器的顺序")

    events: list[str] = []

    @mark("outer", events)
    @mark("inner", events)
    def target() -> str:
        events.append("target")
        return "ok"

    assert target() == "ok"
    print("调用顺序:", events)
    assert events == [
        "enter outer",
        "enter inner",
        "target",
        "exit inner",
        "exit outer",
    ]


@cache
def fibonacci(number: int) -> int:
    """Calculate Fibonacci numbers with standard-library caching."""
    if number < 0:
        raise ValueError("number must be non-negative")
    if number < 2:
        return number
    return fibonacci(number - 1) + fibonacci(number - 2)


def demo_cache() -> None:
    section("缓存装饰器")

    fibonacci.cache_clear()
    value = fibonacci(20)
    info_after_first = fibonacci.cache_info()
    repeated = fibonacci(20)
    info_after_second = fibonacci.cache_info()

    print("fibonacci(20):", value)
    print("第一次缓存信息:", info_after_first)
    print("第二次命中增加:", info_after_second.hits > info_after_first.hits)

    assert value == 6_765
    assert repeated == value
    assert info_after_second.hits == info_after_first.hits + 1


class ManagedResource:
    """A context manager that records acquire, use, and release events."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __enter__(self) -> ManagedResource:
        self.events.append("acquire")
        return self

    def use(self) -> str:
        self.events.append("use")
        return "resource-result"

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> bool:
        self.events.append("release")
        return False


class IgnoreValueError:
    """Suppress only ValueError to demonstrate __exit__ semantics."""

    def __enter__(self) -> IgnoreValueError:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> bool:
        return exc_type is ValueError


@contextmanager
def managed_label(label: str, events: list[str]) -> Iterator[str]:
    """Manage a label with the contextmanager decorator."""
    events.append(f"enter {label}")
    try:
        yield label.upper()
    finally:
        events.append(f"exit {label}")


@contextmanager
def elapsed(events: list[str]) -> Iterator[None]:
    """Record that cleanup happens even when the body raises."""
    started = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - started
        events.append(f"elapsed_non_negative={duration >= 0}")


def demo_context_managers() -> None:
    section("上下文管理器")

    events: list[str] = []
    with ManagedResource(events) as resource:
        result = resource.use()

    print("类协议事件:", events)
    assert result == "resource-result"
    assert events == ["acquire", "use", "release"]

    context_events: list[str] = []
    with managed_label("db", context_events) as label:
        context_events.append(f"use {label}")

    print("contextmanager 事件:", context_events)
    assert context_events == ["enter db", "use DB", "exit db"]

    with IgnoreValueError():
        raise ValueError("this expected error is suppressed")
    print("只抑制预期的 ValueError")

    timing_events: list[str] = []
    try:
        with elapsed(timing_events):
            raise RuntimeError("body failed")
    except RuntimeError:
        timing_events.append("error propagated")

    print("异常时仍清理且继续抛出:", timing_events)
    assert timing_events == ["elapsed_non_negative=True", "error propagated"]


def countdown(start: int) -> Iterator[int]:
    """Yield descending positive integers."""
    current = start
    while current > 0:
        yield current
        current -= 1


def flatten_generator(values: list[Any]) -> Iterator[Any]:
    """Flatten nested lists lazily with yield from."""
    for value in values:
        if isinstance(value, list):
            yield from flatten_generator(value)
        else:
            yield value


def batches(values: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield values in lists with at most size items."""
    if size <= 0:
        raise ValueError("size must be positive")

    batch: list[T] = []
    for value in values:
        batch.append(value)
        if len(batch) == size:
            yield batch
            batch = []

    if batch:
        yield batch


def demo_generators() -> None:
    section("生成器")

    generator = countdown(3)
    first = next(generator)
    second = next(generator)
    remainder = list(generator)
    print("冻结再恢复:", first, second, remainder)

    assert first == 3
    assert second == 2
    assert remainder == [1]

    one_shot = (number * number for number in range(3))
    first_pass = list(one_shot)
    second_pass = list(one_shot)
    print("第一次消费:", first_pass)
    print("第二次消费:", second_pass)

    assert first_pass == [0, 1, 4]
    assert second_pass == []

    nested = [1, [2, [3]], 4]
    flat = list(flatten_generator(nested))
    print("yield from 扁平化:", flat)
    assert flat == [1, 2, 3, 4]

    grouped = list(batches(range(7), 3))
    print("分页生成器:", grouped)
    assert grouped == [[0, 1, 2], [3, 4, 5], [6]]

    try:
        list(batches(range(3), 0))
    except ValueError as exc:
        print("非法批大小:", exc)
    else:
        raise AssertionError("zero batch size should fail")


def transform(
    values: Iterable[T],
    mapper: Callable[[T], U],
) -> Iterator[U]:
    """Lazily map values."""
    for value in values:
        yield mapper(value)


def retain(
    values: Iterable[T],
    predicate: Callable[[T], bool],
) -> Iterator[T]:
    """Lazily retain matching values."""
    for value in values:
        if predicate(value):
            yield value


def demo_lazy_pipeline() -> None:
    section("惰性数据管道")

    even = retain(range(10), lambda number: number % 2 == 0)
    squares = transform(even, lambda number: number * number)
    result = list(squares)
    print("偶数平方:", result)
    assert result == [0, 4, 16, 36, 64]


class FakeClock:
    """A deterministic clock for testing time-based code."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_limiter(
    limit: int,
    window_seconds: float,
    *,
    clock: Callable[[], float] = time.monotonic,
) -> Callable[[], bool]:
    """Build a simple single-instance sliding-window limiter."""
    if limit <= 0 or window_seconds <= 0:
        raise ValueError("limit and window_seconds must be positive")

    timestamps: deque[float] = deque()

    def allow() -> bool:
        now = clock()
        boundary = now - window_seconds

        while timestamps and timestamps[0] <= boundary:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return False

        timestamps.append(now)
        return True

    return allow


def demo_limiter_closure() -> None:
    section("闭包实战：限流器")

    clock = FakeClock()
    allow = make_limiter(2, 10, clock=clock)

    results = [allow(), allow(), allow()]
    print("同一窗口前三次:", results)
    assert results == [True, True, False]

    clock.advance(10)
    after_window = allow()
    print("窗口过期后:", after_window)
    assert after_window is True


def call_all(
    func: Callable[..., R],
    *argument_groups: tuple[Any, ...],
) -> list[R]:
    """Call one function with several positional argument groups."""
    return [func(*group) for group in argument_groups]


def demo_practice_answers() -> None:
    section("综合练习参考实现")

    results = call_all(lambda left, right: left + right, (1, 2), (10, 20))
    print("批量调用:", results)
    assert results == [3, 30]

    counter = make_counter(5)
    print("计数器:", counter(), counter(4))

    fresh_counter = make_counter(5)
    assert fresh_counter() == 6
    assert fresh_counter(4) == 10

    groups = list(batches("abcdefg", 3))
    print("字符串分页:", groups)
    assert groups == [["a", "b", "c"], ["d", "e", "f"], ["g"]]


def main() -> None:
    demos = [
        demo_returns,
        demo_parameters,
        demo_object_sharing,
        demo_mutable_defaults,
        demo_type_hints,
        demo_scope_and_closures,
        demo_recursion,
        demo_lambda_and_higher_order_functions,
        demo_late_binding,
        demo_decorators,
        demo_decorator_order,
        demo_cache,
        demo_context_managers,
        demo_generators,
        demo_lazy_pipeline,
        demo_limiter_closure,
        demo_practice_answers,
    ]

    for demo in demos:
        demo()

    section("完成")
    print(f"{len(demos)} 组实验全部通过。")


if __name__ == "__main__":
    main()

"""面向对象实验：property、对象协议、鸭子类型与 MRO。

运行方式：python examples/oop_lab.py
仅使用 Python 3.11+ 标准库。
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import ClassVar, Generic, Protocol, TypeVar, overload


T = TypeVar("T")


class Account:
    """演示类变量、property 校验和敏感字段脱敏。"""

    created_count: ClassVar[int] = 0

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        type(self).created_count += 1

    @property
    def password(self) -> str:
        return "******"

    @password.setter
    def password(self, value: str) -> None:
        if len(value) < 8:
            raise ValueError("password must contain at least 8 characters")
        self._password = value

    def verify_password(self, candidate: str) -> bool:
        return candidate == self._password

    def __repr__(self) -> str:
        return f"Account(username={self.username!r})"


class Product:
    """用值校验、用户展示、调试展示和相等协议描述商品。"""

    tax_rate: ClassVar[float] = 0.10

    def __init__(self, sku: str, name: str, price: float) -> None:
        self.sku = sku
        self.name = name
        self.price = price

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        numeric_value = float(value)
        if numeric_value < 0:
            raise ValueError("price must be non-negative")
        self._price = numeric_value

    @property
    def price_with_tax(self) -> float:
        return round(self.price * (1 + type(self).tax_rate), 2)

    def __str__(self) -> str:
        return f"{self.name}: {self.price:.2f}"

    def __repr__(self) -> str:
        return (
            f"Product(sku={self.sku!r}, name={self.name!r}, "
            f"price={self.price!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return (
            self.sku,
            self.name,
            self.price,
        ) == (
            other.sku,
            other.name,
            other.price,
        )


class CustomQueue(Generic[T]):
    """一个小型 FIFO 队列，用于练习 Python 容器协议。"""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self._items = list(values)

    def enqueue(self, value: T) -> None:
        self._items.append(value)

    def dequeue(self) -> T:
        if not self._items:
            raise IndexError("dequeue from empty queue")
        return self._items.pop(0)

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek from empty queue")
        return self._items[0]

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)

    @overload
    def __getitem__(self, key: int) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> list[T]:
        ...

    def __getitem__(self, key: int | slice) -> T | list[T]:
        return self._items[key]

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __repr__(self) -> str:
        return f"CustomQueue({self._items!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustomQueue):
            return NotImplemented
        return self._items == other._items


class Prefixer:
    """带配置的可调用对象。"""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(self, text: str) -> str:
        return f"{self.prefix}{text}"


class Sender(Protocol):
    """结构化类型：实现 send 即可，无需显式继承。"""

    def send(self, message: str) -> None:
        ...


class ConsoleSender:
    def send(self, message: str) -> None:
        print(f"console received: {message}")


class MemorySender:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def notify(sender: Sender, message: str) -> None:
    sender.send(message)


class RootProcessor:
    def process(self, trace: list[str]) -> None:
        trace.append("RootProcessor")


class ValidationMixin(RootProcessor):
    def process(self, trace: list[str]) -> None:
        trace.append("ValidationMixin")
        super().process(trace)


class AuditMixin(RootProcessor):
    def process(self, trace: list[str]) -> None:
        trace.append("AuditMixin")
        super().process(trace)


class OrderProcessor(ValidationMixin, AuditMixin):
    def process(self, trace: list[str]) -> None:
        trace.append("OrderProcessor")
        super().process(trace)


class GoodCart:
    """实例容器在初始化时创建，不在类上共享。"""

    def __init__(self) -> None:
        self.items: list[str] = []


def demo_property_and_class_variables() -> None:
    print("property and class variables")

    account = Account("alice", "safe-pass-2026")
    assert account.password == "******"
    assert account.verify_password("safe-pass-2026")
    assert "safe-pass-2026" not in repr(account)
    print(f"account={account!r}, displayed_password={account.password}")

    try:
        Account("bob", "short")
    except ValueError as exc:
        print(f"rejected password: {exc}")

    product = Product("P-100", "Python Book", 100)
    assert product.price_with_tax == 110.0
    print(f"product={product}, price_with_tax={product.price_with_tax:.2f}")

    try:
        product.price = -1
    except ValueError as exc:
        print(f"rejected price: {exc}")

    first_cart = GoodCart()
    second_cart = GoodCart()
    first_cart.items.append("book")
    assert second_cart.items == []
    print(f"cart items are independent: {second_cart.items}")


def demo_magic_methods() -> None:
    print("magic methods")

    queue = CustomQueue(["A", "B", "C"])
    assert len(queue) == 3
    assert queue
    assert queue[0] == "A"
    assert queue[-1] == "C"
    assert queue[0:3:2] == ["A", "C"]
    assert list(queue) == ["A", "B", "C"]
    assert queue == CustomQueue(["A", "B", "C"])
    print(f"queue={queue!r}")
    print(f"slice={queue[0:3:2]}, first_out={queue.dequeue()}")
    print(f"remaining={list(queue)}, length={len(queue)}")

    prefixer = Prefixer("WARN: ")
    assert callable(prefixer)
    print(prefixer("disk is nearly full"))


def demo_duck_typing() -> None:
    print("duck typing")

    console_sender = ConsoleSender()
    memory_sender = MemorySender()
    notify(console_sender, "order created")
    notify(memory_sender, "order created")
    assert memory_sender.messages == ["order created"]
    print(f"memory messages: {memory_sender.messages}")


def demo_mro() -> None:
    print("multiple inheritance and MRO")

    mro_names = [cls.__name__ for cls in OrderProcessor.mro()]
    expected_mro = [
        "OrderProcessor",
        "ValidationMixin",
        "AuditMixin",
        "RootProcessor",
        "object",
    ]
    assert mro_names == expected_mro

    trace: list[str] = []
    OrderProcessor().process(trace)
    assert trace == expected_mro[:-1]
    print(f"MRO: {' -> '.join(mro_names)}")
    print(f"cooperative calls: {' -> '.join(trace)}")


def main() -> None:
    demo_property_and_class_variables()
    print()
    demo_magic_methods()
    print()
    demo_duck_typing()
    print()
    demo_mro()
    print()
    print("all object-oriented assertions passed")


if __name__ == "__main__":
    main()

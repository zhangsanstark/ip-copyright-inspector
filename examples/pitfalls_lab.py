"""Runnable demonstrations for common Python mistakes and their fixes."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable


def mutable_default_wrong(value: str, bucket: list[str] = []) -> list[str]:
    bucket.append(value)
    return bucket.copy()


def mutable_default_fixed(
    value: str, bucket: list[str] | None = None
) -> list[str]:
    actual_bucket = [] if bucket is None else bucket
    actual_bucket.append(value)
    return actual_bucket.copy()


def closure_examples() -> tuple[list[int], list[int]]:
    wrong: list[Callable[[], int]] = [lambda: index for index in range(3)]
    fixed: list[Callable[[], int]] = [
        lambda index=index: index for index in range(3)
    ]
    return [func() for func in wrong], [func() for func in fixed]


def copy_examples() -> tuple[list[list[int]], list[list[int]]]:
    original = [[1], [2]]
    shallow = original.copy()
    deep = deepcopy(original)

    shallow[0].append(99)
    deep[1].append(88)
    return original, deep


def identity_examples() -> tuple[bool, bool]:
    left = [1, 2]
    right = [1, 2]
    return left == right, left is right


def dictionary_contract() -> tuple[str, bool]:
    record = {"name": "demo", "description": None}
    missing = object()
    required_name = record["name"]
    is_owner_absent = record.get("owner", missing) is missing
    return required_name, is_owner_absent


def main() -> None:
    print("mutable default, wrong:")
    print(mutable_default_wrong("a"))
    print(mutable_default_wrong("b"))

    print("mutable default, fixed:")
    print(mutable_default_fixed("a"))
    print(mutable_default_fixed("b"))

    wrong_closures, fixed_closures = closure_examples()
    print("closures:", wrong_closures, fixed_closures)

    original, deep = copy_examples()
    print("copy:", original, deep)

    equal, identical = identity_examples()
    print("equality and identity:", equal, identical)

    required_name, owner_absent = dictionary_contract()
    print("dictionary contract:", required_name, owner_absent)


if __name__ == "__main__":
    main()

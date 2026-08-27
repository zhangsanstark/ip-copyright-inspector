"""Python 3.11+ 基础与容器练习。

运行方式：
    python examples/basics_lab.py

脚本不需要第三方依赖，不读取网络，也不修改本地文件。
所有断言通过后，最后会打印完成提示。
"""

from __future__ import annotations

from copy import deepcopy
from itertools import zip_longest
from typing import Any


def section(title: str) -> None:
    """Print a low-key separator so every experiment is easy to locate."""
    print(f"\n[{title}]")


def demo_types_and_identity() -> None:
    section("类型、对象身份和可变性")

    age = 30
    price = 19.9
    name = "Ada"
    enabled = True

    print(type(age).__name__, type(price).__name__, type(name).__name__)
    print(isinstance(enabled, bool))

    first = [1, 2]
    alias = first
    same_value = [1, 2]

    print("first == same_value:", first == same_value)
    print("first is same_value:", first is same_value)
    print("first is alias:", first is alias)

    alias.append(3)
    print("修改 alias 后 first:", first)

    assert type(age) is int
    assert isinstance(price, float)
    assert first == [1, 2, 3]
    assert first is alias
    assert first is not same_value


def demo_input_conversion_without_interaction() -> None:
    section("模拟 input 字符串转换")

    raw_values = ["42", " 7 ", "bad", "3.14"]
    converted: list[int] = []

    for raw in raw_values:
        try:
            converted.append(int(raw))
        except ValueError:
            print(f"跳过无法转换的整数: {raw!r}")

    print("合法整数:", converted)
    print("bool('False'):", bool("False"))

    text_flag = "false"
    parsed_flag = text_flag.strip().lower() in {"1", "true", "yes", "on"}
    print("显式解析 'false':", parsed_flag)

    assert converted == [42, 7]
    assert bool("False") is True
    assert parsed_flag is False


def demo_strings() -> None:
    section("字符串")

    text = "banana"
    print("find na:", text.find("na"))
    print("rfind na:", text.rfind("na"))
    print("find xy:", text.find("xy"))
    print("count na:", text.count("na"))

    assert text.find("na") == 2
    assert text.rfind("na") == 4
    assert text.find("xy") == -1
    assert text.count("na") == 2

    raw = " java, python,go "
    languages = [part.strip() for part in raw.strip().split(",")]
    print("split + strip:", languages)
    print("join:", " | ".join(languages))
    print("replace two times:", "one one one".replace("one", "1", 2))

    assert languages == ["java", "python", "go"]
    assert " | ".join(languages) == "java | python | go"

    prefix = "Bearer secret-token"
    filename = "report.csv"
    print("remove prefix:", prefix.removeprefix("Bearer "))
    print("remove suffix:", filename.removesuffix(".csv"))
    print("strip chars:", "abbaXabba".strip("ab"))

    assert prefix.removeprefix("Bearer ") == "secret-token"
    assert filename.removesuffix(".csv") == "report"
    assert "abbaXabba".strip("ab") == "X"

    word = "Python"
    checks = {
        "starts_with_py": word.startswith("Py"),
        "ends_with_on": word.endswith("on"),
        "is_alpha": word.isalpha(),
        "123_is_digit": "123".isdigit(),
        "abc123_is_alnum": "abc123".isalnum(),
        "whitespace": " \t\n".isspace(),
    }
    print("字符串判断:", checks)
    assert all(checks.values())

    amount = 1_234_567
    ratio = 0.256
    score = 95.678
    print(f"格式化: amount={amount:,}, ratio={ratio:.1%}, score={score:.2f}")
    assert f"{score:.2f}" == "95.68"

    print("不区分大小写:", "straße".casefold() == "STRASSE".casefold())
    assert "straße".casefold() == "STRASSE".casefold()


def demo_lists() -> None:
    section("列表的增删改查")

    appended = [1, 2]
    append_result = appended.append([3, 4])
    print("append 整体加入:", appended)
    print("append 返回值:", append_result)

    extended = [1, 2]
    extended.extend([3, 4])
    extended.insert(1, 99)
    print("extend 后再 insert:", extended)

    assert appended == [1, 2, [3, 4]]
    assert append_result is None
    assert extended == [1, 99, 2, 3, 4]

    items = [10, 20, 20, 30]
    popped = items.pop(1)
    items.remove(20)
    del items[0]
    print("pop 返回:", popped)
    print("连续删除后:", items)

    assert popped == 20
    assert items == [30]

    items.clear()
    assert items == []

    values = [10, 20, 30]
    values[1] = 99
    values[0:2] = [1, 2, 3]
    print("下标和切片赋值:", values)
    assert values == [1, 2, 3, 30]

    print("enumerate 从 1 开始:", list(enumerate(values, start=1)))
    assert list(enumerate(values, start=1))[0] == (1, 1)

    visited: list[int] = []
    index = 0
    while index < len(values):
        visited.append(values[index])
        index += 1
    print("while 按下标遍历:", visited)
    assert visited == values


def demo_copying() -> None:
    section("浅拷贝和深拷贝")

    original = [[1], [2]]
    shallow = original.copy()
    shallow[0].append(99)
    print("浅拷贝修改后 original:", original)

    assert original == [[1, 99], [2]]
    assert shallow is not original
    assert shallow[0] is original[0]

    source = [[1], [2]]
    independent = deepcopy(source)
    independent[0].append(99)
    print("深拷贝修改后 source:", source)

    assert source == [[1], [2]]
    assert independent == [[1, 99], [2]]
    assert independent[0] is not source[0]

    wrong_matrix = [[0] * 3] * 2
    wrong_matrix[0][0] = 9
    print("乘法创建二维列表的坑:", wrong_matrix)

    right_matrix = [[0] * 3 for _ in range(2)]
    right_matrix[0][0] = 9
    print("推导式创建独立行:", right_matrix)

    assert wrong_matrix == [[9, 0, 0], [9, 0, 0]]
    assert right_matrix == [[9, 0, 0], [0, 0, 0]]


def demo_sorting() -> None:
    section("排序")

    numbers = [3, 1, 2]
    ordered = sorted(numbers)
    print("原列表:", numbers)
    print("sorted 新列表:", ordered)

    sort_result = numbers.sort(reverse=True)
    print("sort 原地修改:", numbers)
    print("sort 返回值:", sort_result)

    assert ordered == [1, 2, 3]
    assert numbers == [3, 2, 1]
    assert sort_result is None

    employees = [
        {"name": "A", "score": 90, "age": 30},
        {"name": "B", "score": 95, "age": 35},
        {"name": "C", "score": 95, "age": 25},
    ]
    employees.sort(key=lambda employee: (-employee["score"], employee["age"]))
    names = [employee["name"] for employee in employees]
    print("分数降序、年龄升序:", names)
    assert names == ["C", "B", "A"]


def demo_tuples_and_unpacking() -> None:
    section("元组与拆包")

    not_a_tuple = (10)
    one_item = (10,)
    print("(10) 的类型:", type(not_a_tuple).__name__)
    print("(10,) 的类型:", type(one_item).__name__)

    assert isinstance(not_a_tuple, int)
    assert isinstance(one_item, tuple)

    record = ("team", ["alice"])
    record[1].append("bob")
    print("元组内的列表仍可变:", record)
    assert record == ("team", ["alice", "bob"])

    first, *middle, last = [1, 2, 3, 4, 5]
    print("星号拆包:", first, middle, last)
    assert (first, middle, last) == (1, [2, 3, 4], 5)

    left, right = 10, 20
    left, right = right, left
    print("交换:", left, right)
    assert (left, right) == (20, 10)

    first_key, second_key = {"name": "Ada", "role": "admin"}
    print("直接拆字典得到键:", first_key, second_key)
    assert (first_key, second_key) == ("name", "role")


def demo_dicts() -> None:
    section("字典")

    user: dict[str, Any] = {"id": 1, "name": "Ada"}
    user["role"] = "admin"
    user["name"] = "Lin"
    print("增改:", user)

    assert user == {"id": 1, "name": "Lin", "role": "admin"}
    assert user.get("missing") is None
    assert user.get("missing", "N/A") == "N/A"

    print("items 遍历:", list(user.items()))
    assert list(user.keys()) == ["id", "name", "role"]

    defaults = {"timeout": 3, "retries": 1}
    custom = {"timeout": 10}
    merged = defaults | custom
    print("字典合并，右侧覆盖:", merged)
    assert merged == {"timeout": 10, "retries": 1}
    assert defaults == {"timeout": 3, "retries": 1}

    groups: dict[str, list[int]] = {}
    groups.setdefault("backend", []).append(1)
    groups.setdefault("backend", []).append(2)
    print("setdefault 聚合:", groups)
    assert groups == {"backend": [1, 2]}

    values = [3, 1, 3, 2, 1]
    unique_in_order = list(dict.fromkeys(values))
    print("保持顺序去重:", unique_in_order)
    assert unique_in_order == [3, 1, 2]


def demo_sets() -> None:
    section("集合")

    required = {"read", "write"}
    owned = {"read", "write", "admin"}

    print("required 是 owned 子集:", required <= owned)
    print("并集:", sorted(required | {"audit"}))
    print("交集:", sorted(owned & {"admin", "read"}))
    print("差集:", sorted(owned - required))
    print("对称差集:", sorted(owned ^ required))

    assert required <= owned
    assert owned - required == {"admin"}
    assert owned & {"admin", "read"} == {"admin", "read"}

    tags = {"python"}
    tags.add("api")
    tags.update(["async", "orm"])
    tags.discard("missing")
    print("集合增删:", sorted(tags))
    assert tags == {"python", "api", "async", "orm"}


def demo_slices_and_ranges() -> None:
    section("切片与 range")

    values = [0, 1, 2, 3, 4, 5]
    samples = {
        "1:4": values[1:4],
        ":3": values[:3],
        "3:": values[3:],
        "::2": values[::2],
        "-2:": values[-2:],
        "::-1": values[::-1],
    }
    print("切片结果:", samples)

    assert samples["1:4"] == [1, 2, 3]
    assert samples["::2"] == [0, 2, 4]
    assert samples["::-1"] == [5, 4, 3, 2, 1, 0]
    assert "abcdef"[4:1:-1] == "edc"

    slice_object = slice(1, 5, 2)
    print("slice 对象:", "abcdef"[slice_object])
    assert "abcdef"[slice_object] == "bd"

    print("range(5):", list(range(5)))
    print("range(2, 8, 2):", list(range(2, 8, 2)))
    print("range(5, 0, -1):", list(range(5, 0, -1)))

    assert list(range(5)) == [0, 1, 2, 3, 4]
    assert list(range(2, 8, 2)) == [2, 4, 6]
    assert list(range(5, 0, -1)) == [5, 4, 3, 2, 1]


def demo_membership() -> None:
    section("in 在不同容器中的含义")

    substring = "py" in "python"
    tuple_member = "aa" in ("a", "b")
    dict_key = "name" in {"name": "Ada"}
    permission_missing = "write" not in {"read"}

    print("字符串检查子串:", substring)
    print("元组检查完整元素:", tuple_member)
    print("字典检查键:", dict_key)
    print("not in 检查不属于:", permission_missing)

    assert substring is True
    assert tuple_member is False
    assert dict_key is True
    assert permission_missing is True


def demo_zip() -> None:
    section("zip")

    names = ["alice", "bob"]
    scores = [95, 88]
    pairs = list(zip(names, scores))
    print("按位打包:", pairs)
    print("直接构造字典:", dict(pairs))

    assert pairs == [("alice", 95), ("bob", 88)]

    truncated = list(zip([1, 2, 3], ["a", "b"]))
    print("默认按最短结束:", truncated)
    assert truncated == [(1, "a"), (2, "b")]

    try:
        list(zip([1, 2, 3], ["a", "b"], strict=True))
    except ValueError:
        print("strict=True 正确发现长度不一致")
    else:
        raise AssertionError("strict zip should reject different lengths")

    padded = list(zip_longest([1, 2, 3], ["a", "b"], fillvalue=None))
    print("zip_longest 补齐:", padded)
    assert padded == [(1, "a"), (2, "b"), (3, None)]

    unpacked_names, unpacked_scores = zip(*pairs)
    print("反向解包:", unpacked_names, unpacked_scores)
    assert unpacked_names == ("alice", "bob")
    assert unpacked_scores == (95, 88)


def demo_comprehensions() -> None:
    section("推导式")

    squares = [number * number for number in range(6)]
    even_squares = [
        number * number
        for number in range(6)
        if number % 2 == 0
    ]
    labels = [
        "even" if number % 2 == 0 else "odd"
        for number in range(5)
    ]

    print("映射:", squares)
    print("筛选:", even_squares)
    print("三元替换:", labels)

    assert squares == [0, 1, 4, 9, 16, 25]
    assert even_squares == [0, 4, 16]
    assert labels == ["even", "odd", "even", "odd", "even"]

    pairs = [(left, right) for left in range(2) for right in range(3)]
    print("双层推导式:", pairs)
    assert pairs == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]

    names = ["alice", "bob"]
    scores = [95, 88]
    score_by_name = {
        name: score
        for name, score in zip(names, scores, strict=True)
    }
    passed = {
        name: score
        for name, score in score_by_name.items()
        if score >= 90
    }
    remainders = {number % 3 for number in range(10)}

    print("字典推导式:", passed)
    print("集合推导式:", sorted(remainders))

    assert passed == {"alice": 95}
    assert remainders == {0, 1, 2}


def safe_ports(raw: str) -> list[int]:
    """Parse, validate, deduplicate, and sort a comma-separated port list."""
    ports: set[int] = set()

    for part in raw.split(","):
        cleaned = part.strip()
        try:
            port = int(cleaned)
        except ValueError:
            continue

        if 1 <= port <= 65_535:
            ports.add(port)

    return sorted(ports)


def flatten_matrix(matrix: list[list[int]]) -> list[int]:
    """Flatten one level of a two-dimensional list."""
    return [item for row in matrix for item in row]


def unique_in_order(values: list[str]) -> list[str]:
    """Keep the first appearance of every string."""
    return list(dict.fromkeys(values))


def summarize_records(records: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate average latency per path in one pass."""
    totals: dict[str, int] = {}
    counts: dict[str, int] = {}

    for record in records:
        path = str(record["path"])
        latency = int(record["latency_ms"])
        totals[path] = totals.get(path, 0) + latency
        counts[path] = counts.get(path, 0) + 1

    return {
        path: totals[path] / counts[path]
        for path in totals
    }


def demo_practice_answers() -> None:
    section("综合练习参考实现")

    ports = safe_ports("8080, 443, bad, 8080, 65536, 80")
    print("合法端口:", ports)
    assert ports == [80, 443, 8080]

    matrix = [[1, 2], [], [3, 4]]
    flat = flatten_matrix(matrix)
    print("二维列表扁平化:", flat)
    assert flat == [1, 2, 3, 4]

    tags = unique_in_order(["api", "db", "api", "cache", "db"])
    print("保持顺序去重:", tags)
    assert tags == ["api", "db", "cache"]

    records = [
        {"path": "/users", "status": 200, "latency_ms": 18},
        {"path": "/orders", "status": 500, "latency_ms": 92},
        {"path": "/users", "status": 200, "latency_ms": 26},
        {"path": "/orders", "status": 200, "latency_ms": 40},
    ]
    averages = summarize_records(records)
    print("路径平均耗时:", averages)
    assert averages == {"/users": 22.0, "/orders": 66.0}


def main() -> None:
    demos = [
        demo_types_and_identity,
        demo_input_conversion_without_interaction,
        demo_strings,
        demo_lists,
        demo_copying,
        demo_sorting,
        demo_tuples_and_unpacking,
        demo_dicts,
        demo_sets,
        demo_slices_and_ranges,
        demo_membership,
        demo_zip,
        demo_comprehensions,
        demo_practice_answers,
    ]

    for demo in demos:
        demo()

    section("完成")
    print(f"{len(demos)} 组实验全部通过。")


if __name__ == "__main__":
    main()

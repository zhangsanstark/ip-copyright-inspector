"""按实际调用顺序观察 map、filter、reduce。只使用标准库。

运行：python examples/higher_order_lab.py
每组都包含断言；刻意触发的 TypeError 会被接住，脚本可完整运行。
"""

from functools import reduce
from itertools import accumulate
from math import prod


def section(number, title):
    print(f"\n{number}）{title}")


def add(accumulator, current):
    return accumulator + current


def multiply(accumulator, current):
    return accumulator * current


def subtract(accumulator, current):
    return accumulator - current


def expect_type_error(label, action):
    """确认错误确实发生；如果没有报错，断言失败提醒我们检查。"""
    try:
        action()
    except TypeError:
        print(label, "-> TypeError（预期内）")
    else:
        raise AssertionError(f"{label}: expected TypeError")


def demo_map():
    section(1, "map：创建时不计算，取值时才处理")
    seen = []

    def square(number):
        seen.append(number)
        print("正在处理", number)
        return number * number

    mapped = map(square, [2, 3])
    print("刚创建好")
    assert seen == []

    first = next(mapped)
    print("取出第一项:", first)
    assert first == 4
    assert seen == [2]

    remaining = list(mapped)
    print("取出剩余项:", remaining)
    assert remaining == [9]
    assert seen == [2, 3]

    exhausted = list(mapped)
    print("再取一次:", exhausted)
    assert exhausted == []
    assert seen == [2, 3]

    paired = list(map(add, [1, 2, 3], [10, 20]))
    print("两组数据按位置相加:", paired)
    assert paired == [11, 22]


def demo_filter():
    section(2, "filter：判断的是布尔值，留下的是原元素")
    checked = []

    def is_even(number):
        decision = number % 2 == 0
        checked.append(number)
        print(f"检查 {number}: {decision}")
        return decision

    filtered = filter(is_even, [1, 2, 3, 4])
    assert checked == []
    first = next(filtered)
    print("第一个保留的元素:", first)
    assert first == 2
    assert checked == [1, 2]
    remaining = list(filtered)
    print("剩下保留的元素:", remaining)
    assert remaining == [4]
    assert list(filtered) == []

    values = [0, None, 2, False, ""]
    truthy = list(filter(None, values))
    non_null = list(filter(lambda value: value is not None, values))
    print("只保留真值:", truthy)
    print("只排除 None:", non_null)
    assert truthy == [2]
    assert non_null == [0, 2, False, ""]


def demo_reduce_steps():
    section(3, "reduce：打印每一轮的两个参数与返回值")
    calls = []

    def add_and_show(accumulator, current):
        result = accumulator + current
        calls.append((accumulator, current, result))
        print(f"原累计={accumulator}, 当前项={current}, 新累计={result}")
        return result

    result = reduce(add_and_show, [1, 2, 3, 4], 0)
    print("最终结果:", result)
    assert result == 10
    assert calls == [(0, 1, 1), (1, 2, 3), (3, 3, 6), (6, 4, 10)]

    loop_result = 0
    for current in [1, 2, 3, 4]:
        loop_result = loop_result + current
    print("普通 for 得到:", loop_result)
    assert loop_result == result


def demo_initial_value():
    section(4, "初始值参加计算；省略时第一项直接作为起点")
    calls = []

    def add_and_record(accumulator, current):
        calls.append((accumulator, current))
        return accumulator + current

    without_initial = reduce(add_and_record, [1, 2, 3, 4])
    print("无初值的调用:", calls)
    print("无初值的结果:", without_initial)
    assert calls == [(1, 2), (3, 3), (6, 4)]
    assert without_initial == 10

    with_100 = reduce(add, [1, 2, 3], 100)
    print("加法从 100 开始:", with_100)
    assert with_100 == 106

    product_from_one = reduce(multiply, [1, 2, 3, 4], 1)
    product_from_zero = reduce(multiply, [1, 2, 3, 4], 0)
    print("乘法从 1 开始:", product_from_one)
    print("乘法从 0 开始:", product_from_zero)
    assert product_from_one == 24
    assert product_from_zero == 0


def demo_empty_and_singleton():
    section(5, "空列表和单元素：有时候一次函数都不会调用")
    calls = []

    def tracked_add(accumulator, current):
        calls.append((accumulator, current))
        return accumulator + current

    assert reduce(tracked_add, [], 10) == 10
    assert reduce(tracked_add, [7]) == 7
    assert calls == []
    print("空列表有初值 -> 10；单元素无初值 -> 7；均未调用处理函数")

    assert reduce(tracked_add, [7], 10) == 17
    assert calls == [(10, 7)]
    print("单元素有初值 -> 17；调用:", calls)

    expect_type_error("空列表无初值", lambda: reduce(tracked_add, []))
    assert reduce(tracked_add, [], None) is None
    print("显式传 None 也算给了初值，空输入直接返回 None")
    expect_type_error("None 加数字", lambda: reduce(add, [1], None))


def demo_order():
    section(6, "减法能看清从左到右的顺序")
    left_to_right = reduce(subtract, [20, 5, 3])
    with_zero = reduce(subtract, [20, 5, 3], 0)
    print("(20 - 5) - 3 =", left_to_right)
    print("((0 - 20) - 5) - 3 =", with_zero)
    assert left_to_right == 12
    assert left_to_right != 20 - (5 - 3)
    assert with_zero == -28


def demo_orders():
    section(7, "累计结果是金额，当前元素是订单字典")
    orders = [
        {"price": 10, "quantity": 2},
        {"price": 3, "quantity": 4},
    ]
    calls = []

    def add_order(total, order):
        subtotal = order["price"] * order["quantity"]
        result = total + subtotal
        calls.append((total, subtotal, result))
        print(f"原合计={total}, 本条={subtotal}, 新合计={result}")
        return result

    result = reduce(add_order, orders, 0)
    print("订单合计:", result)
    assert result == 32
    assert calls == [(0, 20, 20), (20, 12, 32)]
    assert orders == [{"price": 10, "quantity": 2}, {"price": 3, "quantity": 4}]

    def quiet_add_order(total, order):
        return total + order["price"] * order["quantity"]

    expect_type_error("订单累计省略初值", lambda: reduce(quiet_add_order, orders))
    assert sum(order["price"] * order["quantity"] for order in orders) == result


def demo_mistakes():
    section(8, "常见错误：函数、参数、return")
    expect_type_error("传入数字而非函数", lambda: reduce(add(1, 2), [3, 4]))

    def square(number):
        return number * number

    expect_type_error("只接一个参数", lambda: reduce(square, [1, 2]))

    def wrong_add(accumulator, current):
        print("只打印了:", accumulator + current)
        # 故意不 return。第一轮返回 None，下一轮相加时报错。

    expect_type_error("忘记 return", lambda: reduce(wrong_add, [1, 2, 3]))

    consumed = []

    def source():
        for number in [1, 2, 3]:
            consumed.append(number)
            yield number

    total = reduce(add, source(), 0)
    assert consumed == [1, 2, 3]
    assert total == 6
    print("reduce 返回时，有限输入已经被消费:", consumed)


def demo_alternatives_and_answers():
    section(9, "更直接的工具，以及正文自测答案")
    numbers = [1, 2, 3, 4]
    intermediate = list(accumulate(numbers))
    print("sum:", sum(numbers))
    print("prod:", prod(numbers))
    print("每轮累计值:", intermediate)
    assert sum(numbers) == reduce(add, numbers, 0) == 10
    assert prod(numbers) == reduce(multiply, numbers, 1) == 24
    assert intermediate == [1, 3, 6, 10]

    calls = []

    def recorded_add(accumulator, current):
        calls.append((accumulator, current))
        return accumulator + current

    assert reduce(recorded_add, [2, 4, 6], 10) == 22
    assert calls == [(10, 2), (12, 4), (16, 6)]
    assert reduce(multiply, [2, 3, 4], 1) == 24
    assert reduce(multiply, [2, 3, 4], 0) == 0
    assert reduce(subtract, [10, 3, 2]) == 5
    calls.clear()
    assert reduce(recorded_add, [9]) == 9
    assert calls == []
    assert list(filter(lambda value: value is not None, [0, None, 2])) == [0, 2]
    print("正文 7.13 的五道题全部核对通过")


def main():
    demo_map()
    demo_filter()
    demo_reduce_steps()
    demo_initial_value()
    demo_empty_and_singleton()
    demo_order()
    demo_orders()
    demo_mistakes()
    demo_alternatives_and_answers()
    print("\n9 组高阶函数实验全部通过。")


if __name__ == "__main__":
    main()

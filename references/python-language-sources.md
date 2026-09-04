Python 语言官方资料

访问日期：2026-08-27。

这份索引只放官方或一手资料。笔记先用通俗语言解释；需要确认边界、版本差异或完整参数时，再打开原文。

链接中的 `/3/` 指向当前稳定版。目标环境使用 Python 3.11 时，请在文档版本菜单切换到 3.11，避免直接使用较新版本才有的接口。

---

1）基础与容器

- [Python 教程：数据结构](https://docs.python.org/3/tutorial/datastructures.html)：list、tuple、set、dict、推导式和队列建议。
- [Python 教程：字符串](https://docs.python.org/3/tutorial/introduction.html#strings)：下标、切片和字符串基本行为。
- [Python 标准类型](https://docs.python.org/3/library/stdtypes.html)：常用内置类型的完整方法和准确边界。
- [Python 内置函数](https://docs.python.org/3/library/functions.html)：input、id、isinstance、zip 等内置工具。

2）函数与 Python 风格工具

- [Python 教程：定义函数](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)：默认参数、关键字参数、特殊参数和 lambda。
- [Python FAQ：为什么共享默认值](https://docs.python.org/3/faq/programming.html#why-are-default-values-shared-between-objects)：可变默认参数问题的官方解释。
- [functools](https://docs.python.org/3/library/functools.html)：wraps、reduce、缓存和常用高阶函数工具。
- [contextlib](https://docs.python.org/3/library/contextlib.html)：用函数方式编写上下文管理器。
- [表达式参考：生成器表达式](https://docs.python.org/3/reference/expressions.html#generator-expressions)：圆括号生成器表达式的执行规则。
- [表达式参考：yield](https://docs.python.org/3/reference/expressions.html#yield-expressions)：yield 产出值、暂停和恢复的规则。

3）对象模型

- [Python 数据模型](https://docs.python.org/3/reference/datamodel.html)：对象、属性、调用协议和魔术方法的权威说明。
- [Python 教程：类](https://docs.python.org/3/tutorial/classes.html)：self、类变量、实例变量、继承和私有名称修饰。
- [MRO/C3 深入指南](https://docs.python.org/3/howto/mro.html)：需要排查复杂多重继承时再读。
- [typing](https://docs.python.org/3/library/typing.html)：类型提示、Protocol 和现代类型写法。

4）并发

- [asyncio](https://docs.python.org/3/library/asyncio.html)：事件循环、协程、任务和异步 I/O 总入口。
- [threading](https://docs.python.org/3/library/threading.html)：线程、锁和默认 CPython 下的 GIL 说明。
- [multiprocessing](https://docs.python.org/3/library/multiprocessing.html)：进程、进程池、队列和跨平台注意事项。
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)：线程池、进程池和 Future 接口。
- [Python free-threading 指南](https://docs.python.org/3/howto/free-threading-python.html)：Python 3.13 起可选无 GIL 构建的使用和限制。

5）调试与测试基础

- [异常与错误](https://docs.python.org/3/tutorial/errors.html)：异常传播、捕获和自定义异常。
- [pdb 调试器](https://docs.python.org/3/library/pdb.html)：breakpoint、单步执行和查看调用栈。
- [unittest](https://docs.python.org/3/library/unittest.html)：Python 标准库自带的测试框架。

---

6）高阶函数细讲的版本核对

补充核对日期：2026-09-03。以下固定在 Python 3.11 文档，便于与仓库最低运行版本一致；正文的小数据示例另有实际运行验证。

- [functools.reduce](https://docs.python.org/3.11/library/functools.html#functools.reduce)：从左到右累计、两个调用参数、可选初值，以及空输入和单元素的处理。
- [内置 map](https://docs.python.org/3.11/library/functions.html#map)：按需产生转换结果，多组输入时按最短结束。
- [内置 filter](https://docs.python.org/3.11/library/functions.html#filter)：按判断保留原元素，以及函数为 None 时的真假筛选。
- [排序指南](https://docs.python.org/3.11/howto/sorting.html)：key 的单元素输入、一次计算和稳定排序。
- [itertools.accumulate](https://docs.python.org/3.11/library/itertools.html#itertools.accumulate)：逐次产生中间累计结果，与 reduce 的最终结果作对照。

示例材料

本目录仅存放可公开、可复现且不含敏感信息的示例与验证材料。

1）脚本说明

- basics_lab.py：容器、字符串、切片、zip、推导式和综合小练习。
- functions_lab.py：参数、作用域、递归、装饰器、上下文管理器和生成器。
- higher_order_lab.py：逐轮打印 map、filter、reduce 的输入与结果，验证初始值、空输入、错误写法和自测答案。
- oop_lab.py：property、魔术方法、鸭子类型和多重继承。
- concurrency_lab.py：线程池、进程池、锁、asyncio、限流和超时。
- pitfalls_lab.py：可变默认参数、闭包晚期绑定、浅拷贝和对象身份。

2）说明文字的写法

使用普通正文和知识点编号，不使用 Markdown 标题或加粗文字模拟标题。具体见 [排版规则](../note-format.md)。

3）手册中的独立例子

[详细手册](../docs/handbook/README.md) 每章的完整 Python 例子可以独立执行，也可以导出后自己修改：

```powershell
uv run python scripts/check_handbook_examples.py --chapter 08 --show-output
uv run python scripts/check_handbook_examples.py --chapter 08 --export .practice/08
uv run python .practice/08/hb08_reduce_first.py
```

导出只包含明确标记为 runnable 的完整块，不覆盖已存在脚本。后端章节需要项目依赖；片段、选装服务、部署命令不会自动运行。旧的六个实验脚本仍然可以单独使用。

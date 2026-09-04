类型提示与 Pydantic：把“希望收到什么”变成明确的数据规则

本章分两条线：类型提示帮助写代码；Pydantic 在运行时检查数据。两者用到同样的冒号写法，但不是同一个检查机制。

阅读导航：1 类型提示；2 常见组合；3 函数与协议；4 模型字段；5 转换和严格模式；6 验证器；7 嵌套与序列化；8 错误；9 三道完整练习；10 回顾与资料。

完整例子使用 Python 3.11+ 和项目已有依赖。可运行 `python scripts/check_handbook_examples.py --chapter 17 --show-output`，也可以把一个 runnable 代码块单独存为脚本，用 `uv run python 文件名.py` 执行。

1）先分清：注解不是自动执行的 if

1.1 调用普通函数时，解释器不会先检查参数注解

`value: int` 是说明，不会自动插入 `isinstance(value, int)`。
Java 编译器通常会拒绝明显不匹配的实参；普通 Python 调用没有这一步强制约束。
结果可能报错，也可能“算出了一个你没想到的值”。

```python
# runnable: hb17_annotation_runtime
def double(value: int) -> int:
    return value * 2

assert double(3) == 6
assert double("ab") == "abab"
print(double(3), double("ab"))
```

第一次传整数，`* 2` 做数值乘法。
第二次传字符串，`* 2` 做字符串重复。
注解没拦截入口，返回值也不会因为写了 `-> int` 自动变成整数。
静态检查器可以提前指出第二次调用不符合约定；这与运行时实际发生什么要分开看。

1.2 该由谁检查

- IDE 和静态检查器：发现明显类型不匹配，帮助补全和重构。
- Pydantic：外部输入进入系统时解析、转换和校验。
- 业务代码：检查账号是否有权限、记录是否存在等实际规则。
- 数据库：用约束和事务守住并发情况下的数据规则。

不要把全部责任交给任何一层。写了模型，不代表数据库唯一约束就可以不做。

2）先把常用类型写法读顺

2.1 单值、容器、空值

| 写法 | 表达的要求 | 不是在说什么 |
| --- | --- | --- |
| `int` / `float` / `str` / `bool` | 值的预期类型 | 不会自动做运行校验 |
| `list[str]` | 一组字符串 | 不限制列表长度 |
| `dict[str, int]` | 键是字符串，值是整数 | 不规定必须有哪些键 |
| `set[str]` | 不重复的字符串集合 | 不保证遍历顺序 |
| `tuple[int, str]` | 两个位置分别为整数、字符串 | 不是任意长度的元组 |
| `tuple[int, ...]` | 任意长度的整数元组 | 不是恰好两个整数 |
| `str \| None` | 字符串或空值 | 不自动提供默认值 |

`def f(name: str | None)` 仍要求传 `name`。
`def f(name: str | None = None)` 才允许省略。
“可以为 None”和“可以不传”是两条独立规则。

2.2 Iterable、Sequence、Mapping

函数只需要遍历时，参数可写 `Iterable[T]`。
需要下标和长度时，可写 `Sequence[T]`。
只按键读取映射时，可写 `Mapping[K, V]`。
如果确实要 append 或修改字典，再要求具体的可变容器。

这和 Java 面向接口编程很像：别因为调用方现在传 ArrayList，就把所有方法都限制成 ArrayList。

2.3 Any、object、Literal 和 TypedDict

`Any` 让检查器宽松对待后续操作，容易把错误藏起来。
`object` 允许任何对象，但调用具体方法前通常需要收窄类型。
`Literal["queued", "done"]` 限定几个具体值。
`TypedDict` 给普通字典的键写类型说明，运行时仍然是字典，不是 Pydantic 模型。

```python
# runnable: hb17_container_types
from collections.abc import Iterable, Mapping
from typing import Literal, TypedDict

class Row(TypedDict):
    name: str
    status: Literal["queued", "done"]

def clean_names(values: Iterable[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]

def total(counts: Mapping[str, int]) -> int:
    return sum(counts.values())

row: Row = {"name": "A", "status": "queued"}
assert type(row) is dict
assert clean_names(iter([" A ", "", " B "])) == ["A", "B"]
assert total({"ok": 2, "failed": 1}) == 3
print(row)
```

这个例子没有证明 TypedDict 会检查外部 JSON；它只说明注解后的字典还是普通字典。

3）函数类型：什么进来，什么出去

3.1 Callable、TypeVar、Protocol

`Callable[[int], str]` 表示接收一个整数、返回字符串的可调用对象。
`TypeVar` 用来关联输入与输出的类型，不只是随便起一个类型名。
`Protocol` 表示对象需要具备哪些方法，不要求实现类显式继承它。

```python
# runnable: hb17_callable_protocol
from collections.abc import Callable
from typing import Protocol, TypeVar

T = TypeVar("T")

def first(values: list[T]) -> T:
    if not values:
        raise ValueError("empty values")
    return values[0]

def apply(value: int, formatter: Callable[[int], str]) -> str:
    return formatter(value)

class Loader(Protocol):
    def load(self, key: str) -> str: ...

class MemoryLoader:
    def load(self, key: str) -> str:
        return {"a": "alpha"}[key]

def read(loader: Loader) -> str:
    return loader.load("a")

assert first([10, 20]) == 10
assert first(["a", "b"]) == "a"
assert apply(7, lambda number: f"id-{number}") == "id-7"
assert read(MemoryLoader()) == "alpha"
print("function types checked by examples")
```

`first` 的 `T` 表示输入元素是什么类型，返回也保持这种类型。
运行时它仍执行普通 Python 代码，TypeVar 不会自动为每种 T 添加运行时检查。Java 泛型通常也采用类型擦除，不应把两者误读成“Java 会在运行时完整检查所有泛型实参，Python 不会”。

3.2 Annotated、ClassVar、Final

`Annotated[int, ...]` 在基础类型旁附加元信息；FastAPI、Pydantic 可以读取其中的配置。
`ClassVar[int]` 标明这是类级别字段，不是每个实例单独持有的字段。
`Final` 表达不希望重新赋值的意图，不会在普通 Python 运行时给变量上锁。
不要把注解中的约定误当成访问权限或不可变安全机制。

4）Pydantic 模型：每个字段有四个问题

4.1 名字、类型、是否必填、限制条件

以仓库 `CompareRequest` 为例：

- `left_text`：字符串、必填、去掉两端空白后长度至少 1。
- `right_text`：同上。
- `ngram_size`：整数、可以省略、默认 3、范围 1 到 8。
- `extra="forbid"`：没声明的字段不允许悄悄混进来。

`Field(default=3, ge=1, le=8)` 不是一整块“神秘配置”。
default 解决省略字段；ge/le 解决数值范围；description 只是接口说明。

```python
# runnable: hb17_fields
from pydantic import ValidationError
from ip_copyright_inspector.schemas import CompareRequest

request = CompareRequest(left_text="  AB CD  ", right_text="abce")
assert request.left_text == "AB CD"
assert request.ngram_size == 3
assert request.model_dump()["right_text"] == "abce"

for bad in [None, 0, 9]:
    try:
        CompareRequest(left_text="a", right_text="b", ngram_size=bad)
    except ValidationError as error:
        assert error.errors()[0]["loc"] == ("ngram_size",)
    else:
        raise AssertionError("invalid input accepted")
print(request.model_dump())
```

模型清掉的是两端空白，不是所有空白。
仓库算法里的 `normalize_text` 才会继续去掉中间空白并统一大小写。

4.2 默认值本身也可能需要检查

Pydantic 默认不会把字段默认值再按普通输入完整校验一遍。
需要这种检查时用 `validate_default=True`。
仓库默认值 3 合法，但如果你改成 99，不能指望省略字段时一定由 le 自动救场。

```python
# runnable: hb17_validate_defaults
from pydantic import BaseModel, Field, ValidationError

class LooseDefault(BaseModel):
    size: int = Field(default=99, le=8)

class CheckedDefault(BaseModel):
    size: int = Field(default=99, le=8, validate_default=True)

assert LooseDefault().size == 99
try:
    CheckedDefault()
except ValidationError as error:
    assert error.errors()[0]["type"] == "less_than_equal"
else:
    raise AssertionError("default should be rejected")
print("default validation differs")
```

5）类型转换和严格模式

5.1 校验可能同时做整理

外部字符串 `"2"` 可以在默认模式下转为整数 2。
这不是 json.loads 的功劳；JSON 解析只会忠实保留字符串。
如果接口要求客户端必须提交真正的 JSON 数字，就启用严格规则。

```python
# runnable: hb17_strict
from pydantic import ValidationError
from ip_copyright_inspector.schemas import CompareRequest

data = {"left_text": "a", "right_text": "b", "ngram_size": "2"}
assert CompareRequest.model_validate(data).ngram_size == 2
try:
    CompareRequest.model_validate(data, strict=True)
except ValidationError as error:
    assert error.errors()[0]["type"] == "int_type"
else:
    raise AssertionError("strict mode accepted a string")
assert CompareRequest.model_validate(data | {"ngram_size": 2}, strict=True).ngram_size == 2
print("strict input verified")
```

严格模式可以按模型、字段或单次校验调用配置。
它不是“越严格越正确”：例如上游历史接口一直传字符串数字，收紧规则会改变兼容性。
应该先确定接口承诺，再选择转换策略。

6）验证器：在什么时机拿到什么值

6.1 before 看到原始输入，after 看到字段处理后的值

字段验证器默认是 after。
仓库纯空白文本经过 strip 后长度为 0，会先因 min_length 失败，不会再执行后面的自定义检查。
因此错误是 string_too_short，而不是验证器里那句自定义提示。

6.2 跨字段规则用 model_validator

单个字段是否非负，交给 Field 就够了。
“结束值不能小于开始值”同时涉及两个字段，放在模型验证器更自然。

```python
# runnable: hb17_validator_order
from typing import Self
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

trace = []

class Window(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @field_validator("start", mode="before")
    @classmethod
    def see_raw(cls, value):
        trace.append(("before", type(value).__name__))
        return value

    @field_validator("start")
    @classmethod
    def see_parsed(cls, value: int) -> int:
        trace.append(("after", type(value).__name__))
        return value

    @model_validator(mode="after")
    def valid_order(self) -> Self:
        if self.end < self.start:
            raise ValueError("end must not be before start")
        return self

window = Window(start="2", end=5)
assert trace == [("before", "str"), ("after", "int")]
assert window.start == 2
try:
    Window(start=5, end=2)
except ValidationError:
    pass
else:
    raise AssertionError("invalid interval accepted")
print(trace[:2], window.model_dump())
```

先看到字符串，再看到整数，最后检查两个字段的关系。
验证器必须把要继续使用的值返回去；after 模型验证器返回 self。
把数据库查询塞进同步字段验证器，会让一次模型构造藏着外部 I/O，应避免这样设计。

7）嵌套模型与序列化

7.1 一个请求里还有一组对象

`list[Item]` 让 Pydantic 逐项构造 Item，而不是只确认“外面是列表”。
嵌套错误的位置会包含列表下标，方便准确告诉调用方哪一项有问题。

```python
# runnable: hb17_nested_json
from pydantic import BaseModel, Field, ValidationError

class Item(BaseModel):
    title: str = Field(min_length=1)
    weight: int = Field(ge=1)

class Batch(BaseModel):
    request_id: str
    items: list[Item] = Field(min_length=1)
    memo: str | None = None

batch = Batch.model_validate_json('{"request_id":"r1","items":[{"title":"A","weight":"2"}]}')
assert isinstance(batch.items[0], Item)
assert batch.items[0].weight == 2
assert batch.model_dump()["items"][0] == {"title": "A", "weight": 2}
assert "memo" not in batch.model_dump(exclude_none=True)
assert Batch.model_validate_json(batch.model_dump_json()) == batch
try:
    Batch(request_id="r2", items=[{"title": "A", "weight": 0}])
except ValidationError as error:
    assert error.errors()[0]["loc"] == ("items", 0, "weight")
else:
    raise AssertionError("nested error missed")
print(batch.model_dump_json())
```

7.2 model_dump 和 model_dump_json 不一样

前者通常给 Python 数据结构，后者给 JSON 字符串。
HTTP 框架能处理模型，不必先 model_dump_json 再让框架当字符串包一次，避免双重编码。
需要 JSON 兼容的 Python 字典时，可考虑 `model_dump(mode="json")`。
`exclude_none` 忽略空值；`exclude_unset` 忽略调用方没显式设置的字段，含义不同。

8）错误信息既要有用，也别泄露原文

8.1 ValidationError 与 HTTP 422 分属两层

直接构造模型失败得到 ValidationError，不是一个 HTTP 响应。
FastAPI 捕获请求校验问题，才会生成 HTTP 错误。
仓库删除错误详情中的 input，保留 loc/type/msg。
错误日志也需要同样谨慎，不能响应脱敏了、日志却记录整段输入。

8.2 不要拿 model_construct 接外部数据

它是绕过校验构造模型的入口，不是 model_validate 的更快替代名。
如果把不可信输入送给它，后续业务将以为已经得到合法模型。
使用之前必须知道数据已在哪里被检查；不要为了少写几行校验而用它。

9）三道练习，连同完整答案

9.1 练习：页码允许省略，但不能为零

要求 page 默认 1，page_size 默认 20，范围 1 到 100。正常请求与越界请求都要验证。

```python
# runnable: hb17_answer_pagination
from pydantic import BaseModel, Field, ValidationError

class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

assert Pagination().model_dump() == {"page": 1, "page_size": 20}
assert Pagination(page=2, page_size=50).page == 2
for values in [{"page": 0}, {"page_size": 101}]:
    try:
        Pagination(**values)
    except ValidationError:
        pass
    else:
        raise AssertionError("range not enforced")
print("pagination answer passed")
```

9.2 练习：密码确认必须一致，但输出不包含密码

这里仅演示模型边界，不实现密码存储。输入字段之间的关系属于模型级规则。

```python
# runnable: hb17_answer_confirmation
from typing import Self
from pydantic import BaseModel, Field, ValidationError, model_validator

class Registration(BaseModel):
    name: str
    password: str = Field(min_length=8, exclude=True)
    confirm: str = Field(min_length=8, exclude=True)

    @model_validator(mode="after")
    def match(self) -> Self:
        if self.password != self.confirm:
            raise ValueError("password confirmation differs")
        return self

good = Registration(name="Ada", password="example-123", confirm="example-123")
assert good.model_dump() == {"name": "Ada"}
try:
    Registration(name="Ada", password="example-123", confirm="different-456")
except ValidationError:
    pass
else:
    raise AssertionError("mismatch accepted")
print(good.model_dump())
```

排除序列化不等于安全存储，也不保证 repr 或异常日志永不含原文。生产环境另用合适的密码哈希和日志策略。

9.3 练习：输出错误位置，不输出错误输入

```python
# runnable: hb17_answer_errors
from pydantic import ValidationError
from ip_copyright_inspector.schemas import CompareRequest

try:
    CompareRequest(left_text="private-example", right_text="b", ngram_size=9)
except ValidationError as error:
    public_errors = [{"loc": item["loc"], "type": item["type"]} for item in error.errors()]
else:
    raise AssertionError("expected invalid size")
assert public_errors == [{"loc": ("ngram_size",), "type": "less_than_equal"}]
assert "private-example" not in repr(public_errors)
print(public_errors)
```

10）回顾与官方资料

能分别回答：类型注解是谁读取的？默认值何时生效？验证器拿到的是原始值还是解析后的值？序列化给的是字典还是字符串？错误由模型抛出还是 HTTP 框架生成？

本章行为以项目环境验证为准，不意味着安装了文档站的最新版本。

- [Python 3.11 typing](https://docs.python.org/3.11/library/typing.html)
- [Pydantic 模型](https://pydantic.dev/docs/validation/latest/concepts/models/)
- [字段与默认值](https://pydantic.dev/docs/validation/latest/concepts/fields/)
- [验证器次序](https://pydantic.dev/docs/validation/latest/concepts/validators/)
- [严格模式](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/)
- [序列化](https://pydantic.dev/docs/validation/latest/concepts/serialization/)

FastAPI 请求全过程：一份 JSON 怎样变成一次响应

先不要把 FastAPI 记成一排装饰器。更有用的顺序是：收到请求 → 找到路由 → 解析参数、准备依赖并校验 → 调用函数 → 检查输出 → 发送响应。参数校验与依赖解析会相互配合，不应理解成所有参数全部校验完以后才可能执行任何依赖。路由函数只是这条链中的一段。

阅读导航：1 请求和路由；2 参数来源；3 校验与错误；4 返回值；5 依赖；6 同步与异步；7 本仓库全过程；8 完整练习；9 排查与资料。

完整例子使用项目环境里的 FastAPI、Pydantic、SQLAlchemy 和 TestClient 相关依赖，不需要启动网络端口。运行 `python scripts/check_handbook_examples.py --chapter 18 --show-output` 可以集中核对。

1）先看清请求里到底装了什么

1.1 URL、请求方法、请求体不是一件事

假设客户端发送 `POST /items/7?verbose=true`，再附上一段 JSON。`POST` 是请求方法；`/items/7` 是路径；问号后面是查询字符串；JSON 是请求体。

`7` 出现在路径里，通常用来指出“操作哪一个对象”。`verbose=true` 通常用来补充“这次怎么操作或怎么展示”。请求体适合装结构化内容，例如名称、价格和标签。

这些只是常见设计习惯，不是“路径只能放编号”的语法限制。接口双方需要约定哪些数据放哪里。

浏览器里看到的 URL 不包含请求体。拿到一个 URL，也不一定就拥有复现这个请求所需的所有信息。

1.2 装饰器先登记规则，收到请求后才调用函数

导入模块时执行 `@app.get("/health")`，FastAPI 会登记：某个 HTTP 方法与某段路径对应哪个函数。它不会因为看见装饰器，就马上执行一次健康检查。

请求到来以后，框架用方法和路径寻找匹配路由。路径相同而方法不同，也可以是两个不同接口。

固定路径和动态路径可能冲突。例如 `/users/me` 与 `/users/{user_id}`，应先声明固定路径。否则 `me` 可能先被当作 `user_id` 取走，再触发编号校验错误。

1.3 TestClient 能让请求经过这条链，但不需要真实端口

下面不是直接调用 `health()`。`client.get()` 会走应用的路由和响应处理，适合检查接口行为。

```python
# runnable: hb18_health
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

with TestClient(app) as client:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"].startswith("application/json")
    assert client.post("/health").status_code == 405
print("GET 成功；同一路径的 POST 没有登记")
```

`response.json()` 把响应中的 JSON 文本解析成 Python 对象。它不是路由函数内部原封不动的那个字典对象；中间已经经过了响应处理。

1.4 OpenAPI 是接口描述，Swagger UI 是展示它的页面

FastAPI 可以根据路由、参数注解和数据模型生成 OpenAPI 描述。默认的 `/openapi.json` 返回这份结构化 JSON，`/docs` 提供 Swagger UI 页面，让人查看参数并尝试请求；通常还可通过 `/redoc` 查看另一种文档页面。

不是在函数上多写了一个装饰器就另生成了一套业务接口。文档描述的是同一组路由，页面里的试用功能最终仍向实际接口发送请求。

```python
# runnable: hb18_openapi_swagger
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(min_length=1, description="展示名称")

app = FastAPI(title="Inspector API", version="0.1.0")

@app.post("/items/{item_id}", response_model=Item, status_code=201,
          summary="保存一条展示记录")
def create_item(item_id: int, item: Item) -> Item:
    return item

schema = app.openapi()
operation = schema["paths"]["/items/{item_id}"]["post"]
assert schema["info"]["title"] == "Inspector API"
assert operation["summary"] == "保存一条展示记录"
assert operation["parameters"][0]["name"] == "item_id"
assert operation["parameters"][0]["in"] == "path"
assert operation["requestBody"]["required"] is True
assert "201" in operation["responses"]
assert schema["components"]["schemas"]["Item"]["properties"]["name"]["minLength"] == 1

with TestClient(app) as client:
    assert client.get("/openapi.json").json() == schema
    page = client.get("/docs")
    assert page.status_code == 200
    assert "swagger-ui" in page.text.lower()
    assert "/openapi.json" in page.text
    assert client.post("/items/7", json={"name": "A"}).status_code == 201
```

`paths` 描述有哪些路径和方法；`parameters` 记录路径、查询等参数；`requestBody` 描述请求体；`responses` 描述响应；`components.schemas` 保存复用的数据结构。

本例核对了 JSON 和文档 HTML，没有启动浏览器加载页面脚本。默认页面可能引用外部脚本资源；离线环境能获取 HTML，不代表页面里的所有交互资源都已能加载。需要完全离线文档时要另行安排静态资源。

文档本身不是安全边界。关闭 `/docs` 不会关闭业务接口，也不等于给接口加上鉴权。可以按部署需求关闭或修改这些地址，但接口权限要独立设计。

```python
# runnable: hb18_docs_disabled
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.get("/health")
def health():
    return {"status": "ok"}

with TestClient(app) as client:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/health").json() == {"status": "ok"}
```

描述文件与页面关系可对照 [FastAPI 入门文档](https://fastapi.tiangolo.com/tutorial/first-steps/)，地址与元信息配置见 [文档配置](https://fastapi.tiangolo.com/tutorial/metadata/)。

2）参数从哪里来：不要只看变量名猜

2.1 路径参数先由路径模板决定

`@app.get("/items/{item_id}")` 中的花括号告诉框架：这段路径是一个变量。函数中的 `item_id: int` 再告诉框架：希望得到整数。

URL 本质上是文字。请求中的 `7` 会经过解析和校验，函数真正开始执行时拿到的是整数 `7`；请求写成 `abc`，则无法按整数规则通过。

2.2 查询参数通常从问号后面读取

不在路径模板中的普通标量参数，通常按查询参数处理。默认值决定是否允许不提供：`limit: int = 10` 表示缺省时用 10。

`Query(ge=1, le=50)` 表示取到值之后还要检查范围。`Annotated[int, Query(...)]` 的 `int` 是类型部分，后面的 `Query` 是给框架的额外说明。

一个参数是否必填，不是看它的类型能不能为 `None`。`q: str | None` 没有默认值时，仍可能是必填；`q: str | None = None` 才明确允许省略并使用 `None`。

2.3 Pydantic 模型通常表示 JSON 请求体

模型字段不会自动变成 URL 参数。下面的 `body: ItemIn` 表示把请求体解析成 `ItemIn`。调用接口时要使用 `json={...}`，而不是把所有字段都拼到 URL 上。

```python
# runnable: hb18_parameter_sources
from typing import Annotated
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)

app = FastAPI()

@app.post("/items/{item_id}")
def save_item(
    item_id: int,
    body: ItemIn,
    verbose: bool = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return {
        "id": item_id,
        "name": body.name,
        "price": body.price,
        "verbose": verbose,
        "limit": limit,
        "id_type": type(item_id).__name__,
    }

with TestClient(app) as client:
    response = client.post(
        "/items/7?verbose=true&limit=2",
        json={"name": "报告", "price": "12.5"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 7, "name": "报告", "price": 12.5,
        "verbose": True, "limit": 2, "id_type": "int",
    }
    assert client.post("/items/abc", json={"name": "A", "price": 1}).status_code == 422
    assert client.post("/items/7?limit=0", json={"name": "A", "price": 1}).status_code == 422
    assert client.post("/items/7", json={"name": "A", "price": -1}).status_code == 422
print("路径、查询、请求体分别取值，再合成函数参数")
```

这里发生了三次值得注意的转换：路径 `"7"` 变为 `7`；查询 `"true"` 变为 `True`；价格字符串 `"12.5"` 变为 `12.5`。默认校验允许部分合理转换；如果接口必须拒绝字符串价格，需要明确设置严格规则。

2.4 单个标量放进请求体，要明确声明

`count: int` 通常会被看成查询参数。需要 JSON 请求体时可以用 `Body()`。`Body(embed=True)` 又会改变形状：从单个 JSON 数值变成带字段名的 JSON 对象。

```python
# runnable: hb18_body_shape
from typing import Annotated
from fastapi import Body, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/plain")
def plain(count: Annotated[int, Body()]) -> int:
    return count * 2

@app.post("/embedded")
def embedded(count: Annotated[int, Body(embed=True)]) -> int:
    return count * 2

with TestClient(app) as client:
    assert client.post("/plain", json=3).json() == 6
    assert client.post("/embedded", json={"count": 3}).json() == 6
    assert client.post("/plain", json={"count": 3}).status_code == 422
    assert client.post("/embedded", json=3).status_code == 422
print("字段类型相同，请求体形状仍可能不同")
```

Header、Cookie、Form、File 分别对应其他输入位置。不能把“都是字符串”当成可以互相替换的理由；框架必须知道到哪里找。

3）校验失败时，业务函数可能根本没有执行

3.1 422 是入口参数不符合约定，不是所有错误的统称

路径、查询和请求体参数的校验错误，通常会产生 422 响应。错误列表里的 `loc` 告诉你位置，例如 `['body', 'price']`；`type` 告诉你是哪条规则失败。

这与函数执行一半出现数据库故障不同。数据库故障不是“客户端的 price 不合格”，不应为了统一外观一律包装成 422。

入口校验失败时，对应路由函数不会正常进入；但不要推出“之前什么都没有执行”。框架可能已经运行某些依赖，尤其不能把参数校验当作依赖绝无副作用的保证。

3.2 错误响应也可能泄露输入

校验错误中可能包含原始 `input`。文本、口令、令牌等信息不适合无条件返回，更不适合无条件写入日志。

本仓库的自定义错误处理器删除每个错误项的 `input`。这减少了错误响应重复输出原文的风险，但不代表请求原文从未进入程序，也不代表日志系统已经完成脱敏。

4）返回一个对象，到客户端收到 JSON，中间还有一步

4.1 response_model 同时描述输出并检查输出

Java 背景可以把输入模型和输出模型分别对应到请求 DTO、响应 DTO。它们不必与数据库实体一模一样。

`response_model=PublicUser` 会按公开模型生成响应。下面内部返回值里有 `password_hash`，公开响应中没有它。

```python
# runnable: hb18_response_model
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

class PublicUser(BaseModel):
    id: int
    name: str

app = FastAPI()

@app.post("/users", response_model=PublicUser, status_code=201)
def create_user():
    return {"id": 1, "name": "小陈", "password_hash": "demo-only"}

with TestClient(app) as client:
    response = client.post("/users")
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "小陈"}
    assert "password_hash" not in response.text
print("内部数据和公开响应可以不同")
```

过滤响应字段不是口令存储方案。真实口令不能因为最后“不返回”就明文保存。这个例子只演示输出边界。

4.2 输出不符合模型，是服务端的问题

如果路由声明返回用户编号，实际却返回无法转换成整数的文字，说明服务端实现没有兑现自己的输出约定。TestClient 默认会抛出服务端异常，帮助测试发现问题；真实客户端通常看到服务端错误响应。

若主动返回 `Response`、`JSONResponse` 等响应对象，就进入直接响应路径，不要再假设普通返回值的模型校验和过滤照常替你完成。手动响应需要自己保证内容与声明一致。

4.3 状态码不能代替响应内容

201 表示资源创建成功，404 表示目标不存在，503 可以表示暂时无法提供服务。路由正常返回 `{"error": "missing"}` 而没有改状态码，通常仍是 200；客户端不能靠字段名字自动知道 HTTP 层失败了。

需要中断本次请求时可以 `raise HTTPException(...)`。`raise` 与 `return False` 的控制流程不同：前者立即沿异常路径退出，后者只是正常返回一个布尔值。

5）依赖：函数参数可以由框架准备

5.1 Depends 不是自己调用函数，而是登记“这个参数怎么获得”

`token: Annotated[str, Depends(read_token)]` 表示让框架先执行 `read_token`，再把结果交给业务函数。依赖也可以继续声明它自己的路径、查询或请求头参数。

下面把请求头读取、访问检查、业务返回分开。测试替换的是依赖的来源，不需要修改业务函数。

```python
# runnable: hb18_dependencies
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()

def read_token(x_token: Annotated[str | None, Header()] = None) -> str:
    if x_token != "demo-token":
        raise HTTPException(status_code=401, detail="missing or invalid token")
    return x_token

@app.get("/private")
def private(token: Annotated[str, Depends(read_token)]):
    return {"accepted": token == "demo-token"}

with TestClient(app) as client:
    assert client.get("/private").status_code == 401
    assert client.get("/private", headers={"x-token": "demo-token"}).json() == {"accepted": True}
    app.dependency_overrides[read_token] = lambda: "demo-token"
    try:
        assert client.get("/private").status_code == 200
    finally:
        app.dependency_overrides.clear()
print("依赖可独立替换，测试结束要恢复")
```

固定令牌仅用于演示，不是可上线的鉴权系统。它没有用户管理、令牌过期、签名校验等必要部分。

5.2 yield 依赖适合管理一次请求使用的资源

数据库依赖通常在 `yield` 前打开会话，把会话交给请求处理逻辑，在 `yield` 后释放资源。不要把它理解为“yield 后自动提交”：是否提交仍由事务代码决定。

依赖清理与响应发送的具体时机还受到 FastAPI 版本、依赖作用域和流式响应影响。稳妥的写法是让数据库工作在明确的事务边界内完成，不让后台任务或流式生成器偷偷继续使用已经交还的会话。

5.3 lifespan 管理的是应用启动和结束，不是每个请求

一个数据库引擎可以在应用生命周期内复用；一个带事务状态的会话通常按请求或任务创建。这两个生命周期不能混在一起。

使用 `with TestClient(app)`，可以让测试执行应用的 lifespan。只构造客户端但不进入上下文，不应假设启动和清理流程已经执行。

6）async def 不是“所有东西自动异步”

6.1 框架处理的同步路由，与自己调用的同步函数不同

FastAPI 会把普通 `def` 路由等适用场景放在线程池执行，避免它们直接阻塞事件循环。`async def` 路由则在异步执行环境中运行。

但是在 `async def` 里面直接调用 `time.sleep()`、同步数据库函数或者耗时 CPU 函数，框架不会逐行分析并自动替你搬走它们。这个普通函数调用仍会在当前线程中执行。

选择方式应取决于内部调用：使用异步数据库驱动，可以 `await`；使用同步库，可以采用同步路由或明确的线程转交；大量 CPU 计算，应考虑进程或独立任务服务。

6.2 await 暂停的是当前协程，不是免费完成工作

`await session.execute(...)` 表示等待数据库 I/O 的同时允许事件循环运行其他就绪任务。SQL 本身仍需数据库执行，也仍可能争锁、超时或失败。

同一个 AsyncSession 不能因为“都在 await”就交给多个并发任务共享。每个任务应拥有自己的会话，下一章会用完整例子解释原因。

7）沿本仓库走一遍，观察每个中间值

7.1 请求进入前，先把六个位置认出来

`main.py` 接收请求并组织流程；`schemas.py` 描述输入与输出；`similarity.py` 只计算；`database.py` 描述表并提供会话；SQLite 保存汇总记录；客户端接收公开响应。

以 `{"left_text": "  AB CD  ", "right_text": "abce", "ngram_size": "2"}` 为例：左文本原始长度是 9；Pydantic 去首尾空白后变成 `"AB CD"`，长度是 5；算法再移除内部空白并处理大小写，变成 `"abcd"`，长度是 4。

窗口大小字符串 `"2"` 被入口模型转换成整数 `2`。算法得到左集合 `{'ab', 'bc', 'cd'}`，右集合 `{'ab', 'bc', 'ce'}`。交集有 2 个，并集有 4 个，所以得分为 `0.5`。

7.2 得分出现了，还不意味着请求已经成功

算法返回 `SimilarityResult`。路由用其中的数字构造 `ComparisonRecord`，`session.add()` 只是登记对象。`await session.flush()` 才把待插入记录送给数据库，并取得生成的编号。

这个时候记录还在当前事务里。`await session.commit()` 成功后，路由才把保存成功当作正常路径的一部分。出现 SQLAlchemy 异常则回滚并返回 503，不能拿一份其实没保存的记录冒充创建成功。

最后构造 `CompareResponse`，补上默认的方法名与声明。声明明确表示：分数只是字符片段集合的技术相似度，不构成侵权、权属或其他法律结论。

7.3 完整实验：请求经过真实应用，但数据库是临时的

下面会创建临时目录与临时数据库，结束时清理。它不会写入仓库默认数据库，也不会启动真实 HTTP 服务。

```python
# runnable: hb18_real_application
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from ip_copyright_inspector import database
from ip_copyright_inspector.main import app

with TemporaryDirectory(prefix="hb18-") as directory:
    database_path = Path(directory) / "isolated.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path.as_posix()}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    with patch.object(database, "engine", engine), patch.object(database, "async_session_factory", factory):
        with TestClient(app) as client:
            payload = {"left_text": "  AB CD  ", "right_text": "abce", "ngram_size": "2"}
            response = client.post("/api/v1/comparisons", json=payload)
            assert response.status_code == 201
            body = response.json()
            assert body["score"] == 0.5
            assert body["left_normalized_length"] == 4
            assert body["intersection_count"] == 2
            assert body["union_count"] == 4
            assert "不构成" in body["notice"]
            rejected = client.post("/api/v1/comparisons", json=payload | {"ngram_size": 9})
            assert rejected.status_code == 422
            assert all("input" not in item for item in rejected.json()["detail"])
            with closing(sqlite3.connect(database_path)) as connection:
                rows = connection.execute(
                    "SELECT id, score, ngram_size, left_normalized_length FROM comparison_records"
                ).fetchall()
            assert rows == [(body["record_id"], 0.5, 2, 4)]
            print(body)
```

这个实验有三个核对点：响应分数是 0.5；数据库只保存一行汇总；错误输入没有变成第二条记录。测试如果只看状态码，会漏掉后两个问题。

8）三道练习，把规则变成能预测的行为

8.1 练习一：分页的缺省、合法值和错误值

要求：`GET /page` 接收 `limit`，默认 20，范围 1 到 100。先预测省略、`limit=3`、`limit=0`、`limit=abc` 的结果，再运行答案。

```python
# runnable: hb18_answer_query
from typing import Annotated
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/page")
def page(limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return {"limit": limit}

with TestClient(app) as client:
    assert client.get("/page").json() == {"limit": 20}
    assert client.get("/page?limit=3").json() == {"limit": 3}
    assert client.get("/page?limit=0").status_code == 422
    assert client.get("/page?limit=abc").status_code == 422
print("省略使用默认值；0 违反范围；abc 无法转成整数")
```

核对顺序：先找输入位置，再看是否提供，然后做类型处理，最后看范围。`abc` 与 `0` 都失败，但失败原因不是同一条。

8.2 练习二：找不到记录时，不要返回一个“错误字典 + 200”

要求：只有编号 1 存在，其余编号返回 404。完整答案如下。

```python
# runnable: hb18_answer_not_found
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()
records = {1: {"id": 1, "score": 0.5}}

@app.get("/records/{record_id}")
def get_record(record_id: int):
    if record_id not in records:
        raise HTTPException(status_code=404, detail="record not found")
    return records[record_id]

with TestClient(app) as client:
    assert client.get("/records/1").json()["score"] == 0.5
    missing = client.get("/records/2")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "record not found"}
print("不存在是 404，不是内容里写了 error 的 200")
```

如果路径写成 `/records/no`，它在整数校验阶段失败，会是 422；并不是进入查找逻辑以后得到 404。先校验编号，再判断编号对应的记录是否存在。

8.3 练习三：验证输出错误会被测试发现

要求：响应模型必须有整数编号，但业务故意返回 `"not-an-int"`。答案不把它吞成空字典，而是明确断言出现了输出校验错误。

```python
# runnable: hb18_answer_bad_response
from fastapi import FastAPI
from fastapi.exceptions import ResponseValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel

class Result(BaseModel):
    id: int

app = FastAPI()

@app.get("/broken", response_model=Result)
def broken():
    return {"id": "not-an-int"}

with TestClient(app) as client:
    try:
        client.get("/broken")
    except ResponseValidationError as error:
        assert error.errors()[0]["loc"] == ("response", "id")
    else:
        raise AssertionError("错误输出本应被拒绝")
print("输入校验和输出校验是两道不同的检查")
```

9）排查顺序与资料

9.1 一次失败，从最靠近输入的位置往后找

404 先检查 URL 和方法对应的路由；405 检查请求方法；422 看 `detail` 的位置和类型；500 看服务端异常；503 再核对本仓库的数据库失败分支。不要看到一个错误就同时改模型、路由和 SQL。

直接调用业务函数能验证计算，但绕过了 HTTP 解析、入口校验和响应处理。TestClient 能验证应用流程，但仍不能证明代理转发、TLS、真实网络和生产数据库都没有问题。不同测试负责不同范围。

9.2 官方资料

[FastAPI 请求体](https://fastapi.tiangolo.com/tutorial/body/)、[查询参数校验](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)、[响应模型](https://fastapi.tiangolo.com/tutorial/response-model/) 对应输入与输出的具体规则。

[FastAPI 依赖](https://fastapi.tiangolo.com/tutorial/dependencies/)、[yield 依赖](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)、[异步与同步](https://fastapi.tiangolo.com/async/)、[测试](https://fastapi.tiangolo.com/tutorial/testing/) 对应资源生命周期与执行方式。依赖清理时机和测试客户端依赖应以项目锁定版本为准。

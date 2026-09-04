生态工具：先看要解决的问题，再决定引入哪个库

知道一个库的名字，和知道什么时候需要它，是两回事。本章把工具放回具体流程：先处理数据，再找候选，再精细计算，必要时放到后台执行，最后把模型或服务稳定运行。

阅读导航：1 问题拆分；2 NumPy；3 Pandas；4 SimHash；5 MinHash；6 Alembic；7 向量检索；8 Celery；9 Triton；10 三道练习；11 选型与资料。

标记 optional 的 Python 示例需要额外依赖或已有服务，不属于当前基础环境验收，也未执行。runnable 只用标准库或仓库已有代码，可通过 `python scripts/check_handbook_examples.py --chapter 25 --show-output` 运行。

1）先说明本仓库现在真正做了什么

1.1 当前实现是字符片段集合比较

仓库把两段文本标准化，切成字符 n-gram 集合，计算 Jaccard 分数。它不调用向量模型、不使用分布式任务队列，也没有把每次比较交给 GPU。

如果只比较一对短文本，这条直接路径简单、容易核对。引入更多组件并不自动让结果更可靠，反而会增加安装、运行和排查成本。

1.2 文本数量变大以后，问题会发生变化

两段文本比较一次，与在一百万条记录里寻找相似候选，是不同规模的问题。后一种场景常先用索引筛出少量候选，再对候选做更精细的比较。

这时要分别回答：文本如何变成特征；候选怎样找；最终分数怎么算；阈值怎样验证；计算是否需要离线；结果怎样保存和展示。

下面的库分别参与其中一些环节，没有一个名字能把这些问题全部包办。

2）NumPy：大量规则数值，别每个元素都在 Python 循环里处理

2.1 它解决的不是“列表不好用”，而是数值数据的批量操作

Python 列表可以放不同类型对象；NumPy 的 ndarray 通常用统一 dtype 表示一组数值，并记录 shape。这样很多批量运算可以在底层实现中完成。

`shape=(3, 2)` 表示三行两列；`dtype=float64` 表示元素按某种浮点格式存储。shape 决定数据排列，dtype 决定单个元素如何表示，两者不能混为一谈。

NumPy 不保证任何代码都更快。输入很小、频繁转换、使用 object dtype 或算法本身不合适时，收益可能很小。先测具体操作，不要背“快一百倍”。

2.2 数组乘法与列表乘法意思不同

前提：另行安装兼容的 NumPy。下面只在内存里运行，不使用 GPU，也不需要服务。

```python
# optional: hb25_numpy_array_requires_numpy
import numpy as np

scores = np.array([0.2, 0.5, 0.8], dtype=np.float64)
percentages = scores * 100
assert scores.shape == (3,)
assert np.allclose(percentages, [20, 50, 80])
assert [1, 2] * 2 == [1, 2, 1, 2]
assert np.array_equal(np.array([1, 2]) * 2, [2, 4])

matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
row_totals = matrix.sum(axis=1)
column_totals = matrix.sum(axis=0)
assert np.array_equal(row_totals, [3, 7, 11])
assert np.array_equal(column_totals, [9, 12])
print(percentages, row_totals, column_totals)
```

`axis=1` 沿每行的列方向合并，得到每行一个和；`axis=0` 沿行方向合并，得到每列一个和。先画出数据的行列，再读 axis，通常比背“0 是什么、1 是什么”稳。

2.3 切片可能共享底层数据

Python 列表切片通常创建新列表；NumPy 的基本切片通常得到视图，仍引用原数组的数据。修改切片可能改到原数组，需要独立数据时应明确 `.copy()`。

```python
# optional: hb25_numpy_view_requires_numpy
import numpy as np

original = np.array([10, 20, 30])
view = original[1:]
view[0] = 99
assert np.array_equal(original, [10, 99, 30])
independent = original[1:].copy()
independent[0] = 0
assert original[1] == 99
print(original, independent)
```

这不是说所有 NumPy 索引都会返回视图。高级索引等操作有不同规则，遇到共享内存问题应核对具体索引方式。

2.4 与本仓库的关系

若要汇总一大批数值分数、处理固定维度向量或做矩阵运算，NumPy 可能合适。当前算法主要处理字符串和集合，直接换成 ndarray 不会自动加速每一步。

3）Pandas：有列名的表格，筛选、分组、连接更顺手

3.1 DataFrame 不是数据库，但像一张内存中的表

DataFrame 有行、列、索引和各列的数据类型。它适合分析 CSV、批量清洗、按条件筛选与分组统计。

例如有一批比较记录，想看每种窗口大小的平均分，可以用 groupby 表达。它不负责替代数据库事务，也不会自动把修改写回原 CSV。

3.2 筛选与分组的执行过程

前提：另行安装兼容的 Pandas。例子只处理内存数据。

```python
# optional: hb25_pandas_group_requires_pandas
import pandas as pd

frame = pd.DataFrame([
    {"record_id": 1, "ngram_size": 2, "score": 0.4},
    {"record_id": 2, "ngram_size": 2, "score": 0.8},
    {"record_id": 3, "ngram_size": 3, "score": 0.9},
])
mask = frame["score"] >= 0.6
selected = frame.loc[mask, ["record_id", "score"]]
assert selected["record_id"].tolist() == [2, 3]
means = frame.groupby("ngram_size")["score"].mean()
assert abs(means.loc[2] - 0.6) < 1e-12
assert means.loc[3] == 0.9
print(selected.to_dict(orient="records"))
print(means.to_dict())
```

第一步得到布尔掩码，表示每行是否保留；第二步选择满足条件的行与指定列；第三步按窗口大小分组；第四步对每组分数求平均。

`.loc` 按标签选择，`.iloc` 按整数位置选择。索引标签刚好是 0、1、2 时，两种操作看起来相似；标签变成记录编号后，就不能再混用。

3.3 缺失值、连接与内存是常见边界

CSV 的空单元格不一定等于空字符串，可能被解析成缺失值。需要明确哪些字段允许缺失、何时填充，以及填充后对统计有什么影响。

连接两张表时，如果两边连接键都重复，结果行数可能放大。不是只看两份表各有多少行，就能猜出 merge 后还是同样行数。

大文件全部读入 DataFrame 会占内存。可以按块读取、先筛选必要列，或让数据库先完成适合的聚合。Pandas 不是所有规模的统一存储方案。

3.4 与本仓库的关系

API 的单次请求不需要先转 DataFrame。离线统计历史分数分布、比较参数效果、输出人工核对报表时，Pandas 才更贴近问题。

4）SimHash：把特征压成指纹，方便寻找近重复候选

4.1 它不是给任意文本直接生成“版权相似度”

SimHash 先把文本表示为特征，再把特征汇总成固定长度位指纹。比较两份指纹时，常看 Hamming 距离，也就是有多少个二进制位不同。

距离小，可以作为某种近重复候选信号；它不是字符 Jaccard 分数，也不是语义等价或权属判断。

输入特征如何切分、是否保留顺序、怎样加权，都影响指纹。用整段字符串、分词结果、字符片段，得到的行为可能不同。

4.2 先理解 Hamming 距离，再看库调用

```python
# runnable: hb25_hamming
def hamming_distance(left: int, right: int, bits: int = 8) -> int:
    if bits < 1 or not (0 <= left < 2 ** bits and 0 <= right < 2 ** bits):
        raise ValueError("指纹必须落在指定的无符号位宽内")
    return (left ^ right).bit_count()

assert hamming_distance(0b10101010, 0b10101110) == 1
assert hamming_distance(0b00000000, 0b11111111) == 8
assert hamming_distance(0b10101010, 0b10101010) == 0
print("异或后为 1 的位置，就是两份指纹不同的位置")
```

异或比较对应位：相同变 0，不同变 1。bit_count 数其中的 1，所以直接得到位差异数量。

4.3 明确使用字符片段作为特征

前提：另行安装 `simhash` 包。这里故意把特征列表传给库，避免误以为它的默认文本切分一定与本仓库一致。

```python
# optional: hb25_simhash_requires_simhash
from simhash import Simhash

left_features = ["ab", "bc", "cd"]
right_features = ["ab", "bc", "ce"]
left = Simhash(left_features, f=64)
same = Simhash(left_features, f=64)
right = Simhash(right_features, f=64)
assert left.distance(same) == 0
assert 0 <= left.distance(right) <= 64
print("候选指纹距离：", left.distance(right))
```

不能把 `1 - distance / 64` 随手改名为“精确文本相似度”。它只是对指纹距离的一种缩放，不会恢复被压缩前的全部信息。

与仓库结合时，可以先用指纹索引找到候选，再用现有 `compare_texts` 对候选算可解释的字符片段分数。阈值需要用代表性样本验证误报与漏报。

5）datasketch MinHash：用短摘要估计集合的 Jaccard

5.1 它适合的问题与 SimHash 不完全一样

本仓库 Jaccard 明确比较两个集合的交并比。MinHash 针对集合构造摘要，用摘要之间的比较估计 Jaccard，适合不想每次搬运整个大集合的场景。

摘要长度影响估计误差与成本。`num_perm` 增加通常能降低估计波动，但也占更多内存和计算；不是一个必须越大越好的参数。

对比的摘要需要使用兼容的参数和构造方式。特征编码不同、种子或摘要设置不同，不能还当作同一套可比较数据。

5.2 精确值与估计值要一起看

前提：另行安装 `datasketch`。下面不声称这次估计一定恰好等于 0.5。

```python
# optional: hb25_minhash_requires_datasketch
from datasketch import MinHash

left_features = {"ab", "bc", "cd"}
right_features = {"ab", "bc", "ce"}

def summarize(features):
    sketch = MinHash(num_perm=128, seed=1)
    for feature in features:
        sketch.update(feature.encode("utf-8"))
    return sketch

left = summarize(left_features)
right = summarize(right_features)
exact = len(left_features & right_features) / len(left_features | right_features)
estimate = left.jaccard(right)
assert exact == 0.5
assert left.jaccard(summarize(left_features)) == 1.0
assert 0.0 <= estimate <= 1.0
print("精确：", exact, "估计：", estimate)
```

5.3 LSH 返回候选，不承诺每个返回项都满足精确阈值

MinHashLSH 等结构可以根据摘要建立候选索引。它的目标是减少需要详细比较的对象，不是把近似检索变成绝不漏、绝不错的精确查询。

设置某个 threshold，不应解释成“所有真正高于该值的对象必定返回，所有低于该值的对象必定排除”。仍需评估候选召回，再对候选计算目标指标。

若只有少量文本，直接精确比较可能更简单。索引的构建、更新和维护也是成本。

6）Alembic：模型变了，数据库怎样有记录地跟着变

6.1 修改 Python 类，不会自动迁移已存在的表

最初只有 score，后来要增加 reviewed。改 ORM 模型只能描述新的目标结构；老数据库是否已有这列，需要迁移操作来处理。

Alembic 用版本脚本记录升级与回退步骤，数据库中也记录当前迁移版本。这样可以知道某个环境的表结构到了哪一步。

6.2 自动生成的是待检查草稿

典型流程是配置连接与 `target_metadata`，生成 revision，人工检查，再执行 upgrade。自动比较可以发现许多结构差异，但无法理解所有业务意图。

比如把字段改名，它可能看起来像删除旧列再新增一列。直接执行可能丢掉旧数据；正确操作需要判断这是不是一次保留数据的重命名。

下面是迁移脚本正文片段，不是可以直接单独运行的脚本。前提是已初始化 Alembic、设置真实 revision 标识与目标数据库，并检查目标数据库支持的迁移方式。

```python
# fragment: hb25_alembic_migration_body
import sqlalchemy as sa
from alembic import op

def upgrade():
    op.add_column(
        "comparison_records",
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

def downgrade():
    op.drop_column("comparison_records", "reviewed")
```

新列不允许空值时，已有记录怎么填充必须提前安排。这里提供数据库端默认 False，让历史行有值；是否长期保留默认值，还要按应用规则决定。

downgrade 删除列会删除这一列的数据。能写出回退结构脚本，不表示所有数据都能无损回到之前状态。执行迁移前仍要准备备份与恢复验证。

6.3 与本仓库的关系

仓库目前在启动时使用 create_all 创建缺失表，并未建立 Alembic 迁移目录。新增持久字段或演进生产数据库之前，应先设计迁移流程，而不是把启动建表当作永久替代品。

6.4 Tortoise-ORM：另一种异步 ORM 写法，不是 SQLAlchemy 的插件

Tortoise-ORM 同样负责把 Python 对象与数据库表联系起来，提供模型、查询与异步数据库访问。它的查询写法更接近在模型类上直接链式调用，例如 `Review.filter(reviewed=False)`。

SQLAlchemy 提供 Core SQL 表达式与 ORM 等能力，本仓库已经围绕它的引擎、会话和事务组织代码。Tortoise 使用自己的初始化、连接与事务接口，不能把一个 Tortoise 对象直接交给 AsyncSession 管理。

前提：另行安装兼容的 `tortoise-orm` 及其 SQLite 所需依赖。下面是独立脚本，使用内存 SQLite，结束时关闭连接；它不连接仓库默认数据库，也不是现有 API 的替换补丁。

```python
# optional: hb25_tortoise_requires_tortoise_orm
import asyncio
from tortoise import Tortoise, fields
from tortoise.models import Model

class Review(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=100)
    reviewed = fields.BooleanField(default=False)

async def main():
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": [__name__]})
    try:
        await Tortoise.generate_schemas()
        record = await Review.create(title="文本 A")
        assert record.id is not None
        titles = await Review.filter(reviewed=False).values_list("title", flat=True)
        assert titles == ["文本 A"]
        changed = await Review.filter(id=record.id).update(reviewed=True)
        assert changed == 1
        assert await Review.filter(reviewed=True).count() == 1
        await record.delete()
        assert await Review.all().count() == 0
        print("Tortoise 的新增、查询、更新和删除均使用自己的接口")
    finally:
        await Tortoise.close_connections()

asyncio.run(main())
```

`create` 返回新对象；`filter` 逐步描述条件；`values_list(..., flat=True)` 只取一列的值；`update` 返回受影响行数。这些调用需要 await 时才取得异步结果。

选择它并不能免除事务、连接清理、迁移与数据库约束。若确实要替换仓库 ORM，需要重新设计依赖提供、模型映射、迁移和测试；仅因为另一套语法短几行，还不足以证明值得切换。

7）Milvus 与 Chroma：向量近邻检索，不是自动理解文本的魔法

7.1 文本先变成向量，向量数据库再负责存和找

向量是一串固定维度数字。模型可以把文本转成向量，让某种含义接近的文本在选定空间里靠近。向量数据库接收这些向量并建立检索结构。

存储向量与生成向量是两件事。有些工具可以帮你调用默认嵌入函数，但这不代表没有模型下载、算力消耗或数据传输。

同一集合通常要求维度兼容。更重要的是查询与存储使用一致的模型和预处理；两个不同模型碰巧都输出 768 维，也不意味着数字可以直接比较。

7.2 距离指标不同，分数方向也可能不同

余弦相似度通常越大越近；L2 距离通常越小越近。接口返回字段叫 distance 或 score 时，仍要查该索引的具体定义。

向量召回可能找到字面差异很大的语义相关文本；字符 Jaccard 则更直接反映字符片段重叠。两者可以互补，但不要把数值放在同一个阈值下比较。

7.3 Chroma 的最小内存例子，明确传向量避免模型下载

前提：另行安装兼容的 `chromadb`。这个可选例子使用临时内存客户端，并明确提供向量，不请求自动生成嵌入，不启动外部服务。

```python
# optional: hb25_chroma_requires_chromadb
import chromadb

client = chromadb.EphemeralClient()
collection = client.create_collection("hb25-vectors")
collection.add(
    ids=["a", "b"],
    embeddings=[[1.0, 0.0], [0.0, 1.0]],
    documents=["横向示例", "纵向示例"],
)
result = collection.query(
    query_embeddings=[[1.0, 0.0]],
    n_results=1,
    include=["documents", "distances"],
)
assert result["ids"][0] == ["a"]
assert result["documents"][0] == ["横向示例"]
print(result)
```

这两个二维向量是手工构造的，用于观察接口，不表示它们真的编码了中文语义。`result['ids'][0]` 的第一层对应第一条查询，第二层才是该查询找到的候选。

7.4 Milvus 更常出现在需要独立向量服务的方案里

Milvus 提供向量存储、索引与查询能力；部署方式还包括不同规模的服务形态。选型时要同时看数据量、更新频率、过滤条件、运维资源和延迟目标。

下面只是针对已有服务、已有集合的一次只读查询示意。前提是已安装匹配的 pymilvus，服务由你授权的环境提供，集合 `text_vectors` 已有二维向量和 text 字段；本章不建立集合、不启动服务。

```python
# optional: hb25_milvus_existing_service
import os
from pymilvus import MilvusClient

client = MilvusClient(uri=os.environ["MILVUS_URI"], token=os.environ["MILVUS_TOKEN"])
try:
    result = client.search(
        collection_name="text_vectors",
        data=[[1.0, 0.0]],
        limit=3,
        output_fields=["text"],
    )
    print(result)
finally:
    client.close()
```

不同索引、模型和集合结构需要相应配置。这个示例没有固定通用相似度阈值，更没有把检索结果解释成侵权结论。

7.5 与本仓库的关系

目前没有向量生成与检索。如果将来需要语义候选召回，应先选择合适模型、用样本评估、记录模型版本，再考虑接入 Milvus 或 Chroma。不要先装一个向量数据库，再寻找一定要使用它的理由。

8）Celery：请求可以先结束，耗时任务交给独立进程

8.1 它解决的是跨进程任务安排，不是让普通函数更快

一个 API 请求如果要处理很久，可以提交任务，先返回任务编号。独立 worker 从消息代理取任务执行，结果通过选定方式保存或查询。

这与 FastAPI 同进程的轻量后台工作不同。Celery 通常涉及消息代理、worker、任务配置和可能的结果后端，是一套需要运维的系统。

消息代理负责传递任务消息；结果后端负责保存任务结果或状态，二者概念不同。某些部署可以使用同一种产品承担两种角色，但配置与用途仍要分开理解。

8.2 任务函数与提交调用发生在不同时间

前提：另行安装 Celery，并已有授权可用的消息代理和结果后端。以下为任务模块示意，本章不会连接代理、启动 worker 或提交任务。

```python
# optional: hb25_celery_task_module
import os
from celery import Celery
from ip_copyright_inspector.similarity import compare_texts

app = Celery(
    "text_tasks",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
)

@app.task
def compare_task(left_text: str, right_text: str, ngram_size: int = 3):
    result = compare_texts(left_text, right_text, ngram_size=ngram_size)
    return {"score": result.score, "ngram_size": result.ngram_size}
```

导入模块会定义任务，不等于任务已经执行。调用任务的 `.delay(...)` 才会尝试提交消息；返回的是异步结果句柄，不是计算分数字典。

在 HTTP 请求里立即 `.get()` 等待很久，可能把原本想解耦的流程又变回阻塞等待。通常应该返回任务编号，另设结果查询方式和超时策略。

8.3 重试要求任务考虑重复执行

网络中断时，提交方或 worker 可能无法确定上一次操作是否完成。启用重试以后，同一业务动作有可能重复执行，不能默认获得“恰好一次”的效果。

纯相似度计算重复一次主要浪费资源；扣款、发通知、插入记录重复一次可能改变业务结果。可以用业务幂等键、唯一约束和明确状态机减少重复副作用。

不要把数据库会话、连接对象和巨大内存对象直接当任务参数。任务消息应使用适合序列化的小数据，必要时传记录编号，由 worker 自己打开会话读取数据。

8.4 与本仓库的关系

当前短文本比较同步完成，没有 Celery。若扩展为批量文件处理或耗时模型推理，需要先决定任务状态、重试、幂等与结果存储，再接入队列。

9）Triton：这里指模型推理服务器，不是同名内核编程工具

9.1 两个名称容易混淆

NVIDIA Triton Inference Server 用来部署模型推理服务，管理模型、接收请求，并按配置执行推理。

另一个常见的 Triton 指 GPU 内核编程语言与编译器生态。两者都可能涉及 GPU，但解决的问题不同。本章讨论前者。

9.2 它接收的是符合模型约定的张量

模型需要说明输入名称、形状、数据类型和输出。客户端不能随手给一段 JSON 文本，就期望服务器自动知道该用什么 tokenizer、怎样补齐长度。

例如模型期望形状 `[batch, features]`，请求送来 `[features, batch]`，即使元素总数相同，也可能语义错误。类型和形状必须与模型配置一致。

服务可以根据模型和配置使用不同后端与 CPU/GPU 资源。启动一个推理服务器，不等于已经证明计算实际使用 GPU，更不能让本仓库的普通集合运算自动转为 GPU 计算。

9.3 一次实际接入要补齐哪些环节

先取得可合法使用且适合目标任务的模型；在本地验证输入输出；导出或选择服务器支持的格式；配置模型仓库与资源；启动独立服务；客户端按约定发送张量；检查延迟、批处理和错误行为。

本仓库目前没有模型文件与推理请求，因此这里不提供假装可运行的客户端代码。没有模型名称、输入定义与服务地址时，写一个 `infer(...)` 调用只会隐藏真正缺失的条件。

9.4 与相似度流程的关系

如果以后用模型生成文本向量，Triton 可能负责“文本经过预处理后的张量 → 模型输出”。向量数据库负责“向量 → 近邻候选”。现有算法负责“候选文本对 → 字符片段分数”。

这三步可以存在于同一方案，但不要求一定全部引入。先证明新增组件解决了真实问题，再承担它带来的维护工作。

10）三道练习，先用小数据验证概念

10.1 练习一：精确集合分数，与位指纹距离不同

要求：比较两个集合，得到 Jaccard 0.5；再计算两份八位指纹的位差异。答案把两个结果保留为不同字段，不混成同一种分数。

```python
# runnable: hb25_answer_metrics
left = {"ab", "bc", "cd"}
right = {"ab", "bc", "ce"}
intersection = left & right
union = left | right
jaccard = len(intersection) / len(union)
left_fingerprint = 0b10101010
right_fingerprint = 0b10101110
bit_distance = (left_fingerprint ^ right_fingerprint).bit_count()
report = {"jaccard": jaccard, "hamming_distance": bit_distance}
assert report == {"jaccard": 0.5, "hamming_distance": 1}
print(report)
```

第一项需要集合交并；第二项只需要两个整数指纹。指纹已经压缩了特征信息，不能从位差异反推出原集合的完整交并计数。

10.2 练习二：手算向量余弦相似度，并拒绝零向量

要求：相同方向得 1，正交得 0，反方向得 -1。零向量没有可用于除法的长度，因此明确拒绝。

```python
# runnable: hb25_answer_cosine
from math import isclose, sqrt

def cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        raise ValueError("向量必须非空且维度相同")
    left_length = sqrt(sum(value * value for value in left))
    right_length = sqrt(sum(value * value for value in right))
    if left_length == 0 or right_length == 0:
        raise ValueError("零向量不能计算此处定义的余弦相似度")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    return dot / (left_length * right_length)

assert isclose(cosine([1, 0], [2, 0]), 1.0)
assert isclose(cosine([1, 0], [0, 1]), 0.0)
assert isclose(cosine([1, 0], [-1, 0]), -1.0)
try:
    cosine([0, 0], [1, 0])
except ValueError:
    pass
else:
    raise AssertionError("零向量必须被拒绝")
print("方向相同、正交、相反分别得到 1、0、-1")
```

这个例子使用有限普通数值。真实数值接口还应检查 NaN、无穷值和溢出风险。维度相同只保证能按位置计算，不保证两个向量来自兼容模型。

10.3 练习三：先候选筛选，再精确排序

要求：用“是否共享至少一个二字符片段”作为小型候选条件，再用真实仓库算法排序。它不是生产索引，只让执行顺序清楚可见。

```python
# runnable: hb25_answer_candidate_pipeline
from ip_copyright_inspector.similarity import character_ngrams, compare_texts

query = "abcd"
documents = {"same": "abcd", "near": "abce", "far": "wxyz"}
query_features = character_ngrams(query, 2)
candidates = {
    document_id: text
    for document_id, text in documents.items()
    if query_features & character_ngrams(text, 2)
}
ranked = sorted(
    ((document_id, compare_texts(query, text, ngram_size=2).score)
     for document_id, text in candidates.items()),
    key=lambda item: (-item[1], item[0]),
)
assert set(candidates) == {"same", "near"}
assert ranked == [("same", 1.0), ("near", 0.5)]
assert "far" not in dict(ranked)
print(ranked)
```

这里筛选本身仍遍历全部文档，所以并没有建立高效索引。它只是把“候选生成”与“最终打分”分成两步。换成 SimHash、MinHash 或向量索引时，需要重新评估哪些对象可能在第一步被漏掉。

11）最后用几个具体问题约束选型

11.1 先说负载，再说库名

数据是规则数值还是带列名的表格？需要精确交并还是近似候选？数据量有多大，更新多频繁？一条请求能等多久？能否接受额外服务？失败以后怎样恢复？这些答案比“哪个库最火”更能决定工具。

新增库之前做一个小型验证：准备正常样本、边界样本与会误判的样本；记录输入、结果和耗时；比较现有方案；再判断引入成本是否值得。

任何技术相似度、向量距离或候选排序，都不能单独构成侵权、权属或其他法律结论。工具越多，也不能越过这个边界。

11.2 官方资料

[NumPy 基础](https://numpy.org/doc/stable/user/absolute_beginners.html)、[Pandas 入门示例](https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html) 对应数组和表格操作；可选示例未安装额外包执行。

[simhash 项目](https://github.com/1e0ng/simhash)、[datasketch MinHash](https://ekzhu.com/datasketch/minhash.html)、[MinHash LSH](https://ekzhu.com/datasketch/lsh.html) 对应近重复指纹、集合估计与候选检索。

[Alembic 自动生成](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)、[Milvus 快速说明](https://milvus.io/docs/quickstart.md)、[Chroma 入门](https://docs.trychroma.com/docs/overview/getting-started) 对应迁移与向量存储；客户端接口需与实际选择的服务和版本核对。

[Tortoise-ORM 示例](https://tortoise.github.io/examples.html) 对应另一种异步 ORM 的模型与查询流程；本仓库仍使用 SQLAlchemy，没有执行替换。

[Celery 初始流程](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html)、[NVIDIA Triton Inference Server](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html) 对应跨进程任务和模型服务；本章没有启动消息代理、worker、向量服务或推理服务。

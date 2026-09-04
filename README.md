IP Copyright Inspector

IP 版权检测、内容权属分析与合规审查资料库。

1）目录说明

- docs：Python、后端工程和安全驾驶专题记录。
- examples：可直接运行的基础、函数、面向对象、并发和排错实验。
- src/ip_copyright_inspector：最小文本相似度检测 API。
- tests：相似度、数据模型、HTTP 接口和数据库事务测试。
- references：语言组件、法规和公开资料索引。
- scripts：笔记格式检查工具。

2）推荐阅读顺序

1. docs/00-java-to-python-map.md
2. docs/01-python-basics.md
3. docs/02-functions-pythonic.md
4. docs/03-object-oriented.md
5. docs/04-concurrency.md
6. docs/05-backend-engineering.md
7. docs/06-practice-roadmap.md
8. docs/07-debugging-pitfalls.md
9. docs/08-memory-cards.md
10. docs/09-driving-license-subject-four.md
11. docs/10-driving-license-subject-four-review.md

3）直接运行标准库实验

这些脚本只需要 Python 3.11 或更高版本：

```powershell
python examples\basics_lab.py
python examples\functions_lab.py
python examples\higher_order_lab.py
python examples\oop_lab.py
python examples\concurrency_lab.py
python examples\pitfalls_lab.py
```

也可以一次运行全部标准库实验：

```powershell
python scripts\run_all_labs.py
```

4）使用 uv 运行后端示例

```powershell
uv sync --locked
uv run pytest
uv run uvicorn ip_copyright_inspector.main:app --reload
```

启动后访问 http://127.0.0.1:8000/docs，可在自动生成的接口页面提交两段文本进行比较。

5）只有 Python 和 pip 时

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn ip_copyright_inspector.main:app --reload
```

6）运行笔记格式检查

```powershell
python scripts\check_note_format.py
```

7）内容约定

- 每个主题使用独立的 Markdown 文件。
- 引用外部内容时记录标题、作者、链接与访问日期。
- 明确区分事实、推断与待验证事项。
- 不提交账号凭据、令牌、个人隐私或组织内部资料。
- 所有笔记使用普通正文，按 `1）`、`2）` 区分知识点，按 `2.1`、`2.2` 细分；不使用 Markdown 标题或加粗文字模拟标题。
- 详细排版规则见 [note-format.md](note-format.md)。
- 文本相似度结果只是技术指标，不构成版权归属、授权范围或侵权结论。

8）使用方式

克隆仓库后，可直接使用任意 Markdown 编辑器维护内容。

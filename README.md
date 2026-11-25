# 交易所文档 QA Agent

面向交易所文档的智能问答应用。前端用 Streamlit，后端用 FastAPI。问答由 LangGraph Supervisor 把问题分给知识库、来源追溯或交易所公告 Agent；知识库使用本地 BGE 向量和 Chroma，大模型走 DeepSeek 的 OpenAI 兼容接口。用户、会话和消息存在 MySQL，热点会话和消息用 Redis 缓存，Agent 多轮状态用 SQLite checkpoint 按 `thread_id` 保留。

## 功能

- 邮箱注册、登录，JWT 鉴权，密码使用 `pwdlib` 哈希加密后入库。
- 按用户保存会话：新建、切换历史会话、删除会话、清空当前对话。
- 读取 `data/` 中的 PDF、TXT、CSV、DOCX，构建 Chroma 向量库。
- 知识库问答走 RAG 图：MMR 检索、相近文本块去重、资料是否充分的判断、查询改写（最多三次检索）、生成回答。
- Supervisor 按问题路由到知识库问答、来源追溯或交易所公告 Agent。
- 来源追溯返回答案对应的文件名、页码和原文片段。
- 上交所、深交所最新公告走官网实时接口，不查本地向量库。
- 每轮问答把用户问题和助手回答写入 MySQL，并记录 token、耗时、工具名和相关文档。
- 评估脚本对测试问题统计工具选择正确率、回答正确率、检索相关度、延迟、token 用量和失败率。

## 架构

```text
Streamlit（app.py）
        │ HTTP，Bearer Token
        ▼
FastAPI（backend/main.py）
        ├── /api/auth          注册、登录、当前用户
        ├── /api/conversation  会话列表、查询、删除
        ├── /api/messages      消息列表、删除
        └── /api/chat/qa       问答
                │
                ├── MySQL（users / conversations / messages）
                ├── Redis（会话与消息缓存，默认 1 小时）
                └── LangGraph Agent（agent/agent.py）── SQLite checkpoint
                        │
                        ▼
                Supervisor（只负责路由）
                        ├── rag Agent ─────────── profile_search
                        ├── source Agent ──────── return_document_sources
                        └── announcement Agent ── sse_latest_announcements
                                                 szse_latest_announcements
                        │
                        ├── RAG 图（rag/rag.py）── Chroma（vector_db/）
                        ├── 上交所官网实时接口
                        └── 深交所官网实时接口
```

评估入口 `evaluation/evaluate.py` 直接调用编译后的 Agent 图，不经过 FastAPI。rag / source 类问题通过 `retrieve_for_evaluation` 取出检索文档，用于相关性打分。问答接口也会在调用了知识库类工具时写入检索到的文档。

## 项目结构

```text
Product-QA-Agent/
├── agent/
│   ├── agent.py          # Supervisor 多 Agent 图、SQLite 会话记忆、流式输出
│   └── tools.py          # RAG、来源追溯、上交所和深交所公告工具
├── rag/
│   ├── ingest.py         # 文档加载、切分和向量库构建
│   └── rag.py            # RAG StateGraph、检索、改写、回答、来源追溯与评估检索接口
├── backend/
│   ├── main.py           # FastAPI 入口，挂载各路由
│   ├── api/              # auth、chat、conversation、message
│   ├── services/         # Agent 调用封装（限流与超时）
│   ├── crud/             # 用户、会话、消息的数据库操作
│   ├── cache/            # Redis 缓存读写
│   ├── schemas/          # 请求与响应模型
│   ├── db/               # SQLAlchemy 模型与建表 SQL
│   ├── core/             # MySQL、Redis 连接
│   └── utils/            # JWT、密码、当前用户、文档判断
├── evaluation/
│   ├── dataset.py        # 评估测试集
│   ├── evaluate.py       # 跑测试、汇总指标并写出 results.json / summary.json
│   ├── metrics.py        # 工具正确率、延迟、token、LLM 裁判打分等
│   └── results.py        # 读取并打印已保存的评估结果
├── tests/                # API 与服务测试
├── data/                 # 待索引的知识库文档（本地目录，不提交）
├── models/               # 本地 BGE 模型目录（不提交）
├── vector_db/            # Chroma 持久化数据（由 rag/ingest.py 生成，不提交）
├── app.py                # Streamlit 前端
├── Dockerfile            # 应用镜像：安装依赖，默认以 Streamlit 启动
├── docker-compose.yml    # 编排 backend（8000）与 frontend（8501）
├── requirements.txt
├── .env                  # 本地运行配置（不提交）
└── .env.docker           # Docker 运行配置（不提交）
```

运行时会在当前工作目录创建 `langgraph_checkpoints.sqlite` 及其 SQLite 辅助文件，用于保存 Agent 图状态。删除会话时会按 `thread_id` 清理对应 checkpoint。不要手动删除这些文件，除非确认要清除所有已持久化的 Agent 状态。

评估脚本会在当前工作目录写出 `results.json` 和 `summary.json`。

## 环境要求

- Python 3.10 或更高版本（Docker 镜像使用 Python 3.11）
- MySQL，库名 `exchange_qa_agent_db`，表结构见 `backend/db/tables.sql`
- Redis，默认 `localhost:6379`，数据库 0
- 可访问 DeepSeek API
- 本地可用的 BGE embedding 模型（路径由 `MODEL_DIR` 指定）

## 安装与配置

创建并激活虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

在 MySQL 中创建数据库并执行建表脚本：

```sql
CREATE DATABASE exchange_qa_agent_db DEFAULT CHARSET utf8mb4;
```

```bash
mysql -u root -p exchange_qa_agent_db < backend/db/tables.sql
```

数据库连接写在 `backend/core/db_config.py` 的 `ASYNC_DB_URL`，使用 `mysql+aiomysql`。请改成自己的主机、账号和密码。Redis 地址写在 `backend/core/redis_config.py`，默认本机 `6379`。

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=your_deepseek_api_key
MODEL_DIR=D:/path/to/bge-small-zh-v1.5
SECURITY_KEY=your_jwt_secret
```

`OPENAI_API_KEY` 用于访问 DeepSeek；代码里指定了 `https://api.deepseek.com/v1` 和 `deepseek-chat`。`MODEL_DIR` 必须指向本地 BGE 模型目录，Windows 路径建议使用正斜杠。`SECURITY_KEY` 用于签发 JWT，算法 `HS256`，有效期 60 分钟。

Docker 部署额外使用 `.env.docker`。容器内模型通过挂载访问，`MODEL_DIR` 应写成容器路径，例如 `/app/models/bge-small-zh-v1.5`。

## 构建知识库

将 PDF、TXT、CSV 或 DOCX 文件放入项目根目录的 `data/`。`rag/ingest.py` 按当前工作目录读取 `../data`，因此需要在 `rag/` 目录下执行：

```bash
cd rag
python ingest.py
```

脚本使用 `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)` 切分文档，以本地 BGE 模型生成向量，并将 Chroma 数据写入项目根目录的 `vector_db/`。

新增或修改 `data/` 中的文件后，需要再次执行该命令更新向量库。

## 启动应用

先启动 MySQL 和 Redis，再在项目根目录启动后端：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

另开一个终端启动前端：

```bash
streamlit run app.py
```

前端默认请求 `http://127.0.0.1:8000/api`，可用环境变量 `API_URL` 修改。打开 Streamlit 显示的本地地址，注册并登录后即可提问。不要使用 `python app.py` 启动。

接口文档在后端启动后访问 `http://127.0.0.1:8000/docs`。

### 主要接口

除 `/api/auth/register`、`/api/auth/login` 和 `/api/chat/health` 外，其余接口需要请求头 `Authorization: Bearer <access_token>`。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register` | 查询参数：`user_name`、`email`、`password` |
| POST | `/api/auth/login` | 查询参数：`email`、`password`，返回 `access_token` |
| GET | `/api/auth/me` | 当前用户 |
| GET | `/api/chat/health` | 健康检查 |
| POST | `/api/chat/qa` | 问答。JSON：`question`、`thread_id`。可选查询参数 `conversation_id` |
| GET | `/api/conversation/list` | 当前用户的会话列表 |
| GET | `/api/conversation/check` | 查询参数：`conversation_id` |
| DELETE | `/api/conversation/clear` | 查询参数：`conversation_id`，同时删除 Agent checkpoint |
| GET | `/api/messages/check` | 查询参数：`conversation_id` |
| DELETE | `/api/messages/clear` | 查询参数：`conversation_id`、`message_id` |

`question` 长度 1–2000，`thread_id` 长度 1–100。新会话不传 `conversation_id`，后端会建会话并用问题作为标题。

### 使用 Docker Compose

先准备好本地 `models/`、`vector_db/`、`data/` 以及 `.env.docker`，然后在项目根目录执行：

```bash
docker compose up --build
```

后端映射本机 `8000`，前端映射本机 `8501`。前端容器内的 `API_URL` 为 `http://backend:8000/api`。`models`、`vector_db`、`data` 和 SQLite checkpoint 通过 volume 挂载进后端容器，不会打进镜像。

当前数据库连接写在代码里并指向 `localhost`。容器里的 `localhost` 不是宿主机，Compose 里的 `DB_HOST` 也没有被 `backend/core/db_config.py` 读取。在 Docker 中连宿主机 MySQL 时，需要把连接串改成容器能访问的地址。

## 使用说明

- 未登录时前端只显示登录和注册。登录成功后拉取 `/api/auth/me`，侧边栏展示用户名和邮箱。
- Token 失效（HTTP 401）时前端清空登录态并回到登录页。退出登录只清前端状态，服务端 JWT 在过期前仍然有效。
- Supervisor 根据当前问题路由到一个专职 Agent，不会直接生成最终答案。
- 文档内容、业务规则或制度问题由 rag Agent 处理，通过本地知识库检索回答。
- 询问来源、依据、原文或页码由 source Agent 处理，返回相关文件、页码与原文片段。
- 明确询问上交所或深交所的最新或近期公告时，由 announcement Agent 调用对应官网接口。
- 各专职 Agent 只有对应工具可用。模型发出工具调用时，LangGraph 执行工具后将结果交回同一个 Agent 生成答复；不需要工具时直接结束。
- 每个浏览器会话有一个 `thread_id`。已有会话继续提问时携带 `conversation_id`，后端沿用该会话的 `thread_id` 读取 SQLite 中的历史状态。
- 侧边栏可以新建会话、打开历史会话或删除会话。「清空当前对话」会删除当前会话记录。

## 评估

先完成知识库构建并配置好 `.env`，然后在项目根目录运行：

```bash
python -m evaluation.evaluate
```

脚本会遍历 `evaluation/dataset.py` 中的测试用例，调用 Agent 作答，并计算：

- 平均延迟
- 工具选择正确率
- 回答正确率（由 DeepSeek 按标准答案裁判）
- 平均 token 用量（输入 / 输出 / 合计）
- rag / source 问题的检索相关度
- 失败率

结果写入当前目录的 `results.json` 和 `summary.json`。可用下列命令再次查看：

```bash
python -m evaluation.results
```

评估会按用例创建独立的 `thread_id`（形如 `eval_0`），并写入 SQLite checkpoint。这条路径不写 MySQL，也不需要登录。

## 依赖说明

`requirements.txt` 列出运行当前代码所需的包。评估脚本复用 LangChain、LangGraph 和 DeepSeek，没有单独的第三方包。若要锁定已验证环境，可在虚拟环境中执行 `pip freeze > requirements.lock.txt`，部署时使用该锁定文件。

## 注意事项

- `.env` 与 `.env.docker` 包含密钥，切勿提交到版本库。
- `backend/core/db_config.py` 中的数据库账号口令同样不要提交到公开仓库；部署前改成环境对应的连接串。
- `data/`、`models/` 和 `vector_db/` 都是本地资产，当前被 `.gitignore` 排除。
- 应用在导入 RAG 模块时会加载本地 embedding 模型；首次加载可能较慢。
- SQLite checkpoint、MySQL 消息表和 Redis 缓存都可能包含对话内容，分享或清理项目前按敏感数据处理。
- `results.json` / `summary.json` 可能包含问题、模型回答和检索原文，不要提交。

## License

This project is for learning and demonstration purposes.

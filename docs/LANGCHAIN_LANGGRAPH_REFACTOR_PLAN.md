# Galatea LangChain/LangGraph 重构方案

> 本文档记录将 Galatea 项目升级为 LangChain + LangGraph 架构的完整方案。

## 目录

1. [当前架构分析](#当前架构分析)
2. [新目录结构](#新目录结构)
3. [核心概念说明](#核心概念说明)
4. [模块职责说明](#模块职责说明)
5. [迁移路径](#迁移路径)
6. [部署方案](#部署方案)

---

## 当前架构分析

### 现有结构

```
galatea_server/app/
├── services/
│   ├── llm_service.py      # 直接调用 OpenAI SDK
│   ├── agent_service.py    # 业务逻辑 + 流式控制 + TTS 调度
│   ├── session_service.py
│   ├── tts_service.py
│   └── tts_model_service.py
├── infrastructure/managers/
│   └── session_manager.py  # 会话存储 + 音频队列 + 排序
└── utils/
    └── text_buffer.py      # 文本缓冲（句子检测）
```

### 存在的问题

| 现状 | 问题 |
|------|------|
| `LLMService` 直接调用 OpenAI SDK | 无法利用 LangChain 的 LLM 抽象、工具绑定、回调机制 |
| `ChatSession.history` 自己管理消息历史 | LangGraph 有自己的 State 管理，会产生重复 |
| `agent_service` 混合了消息处理、流式控制、TTS 调度 | 职责过多，难以扩展工具调用逻辑 |
| 无持久化 | 服务重启后会话丢失 |

---

## 新目录结构

```
galatea_server/
├── app/
│   │
│   ├── agents/                          # 🆕 LangGraph Agents
│   │   ├── __init__.py                  # 导出 chat_agent
│   │   ├── state.py                     # AgentState 定义
│   │   ├── graph.py                     # Agent 图构建
│   │   ├── nodes.py                     # 图节点实现
│   │   └── tools/                       # Agent 可用工具
│   │       ├── __init__.py              # get_all_tools()
│   │       ├── search.py                # 搜索工具
│   │       └── ...                      # 其他工具
│   │
│   ├── memory/                          # 🆕 记忆系统
│   │   ├── __init__.py                  # 导出 memory_store, checkpointer
│   │   ├── base.py                      # MemoryStore 抽象接口
│   │   ├── chroma_store.py              # Chroma 实现（嵌入式向量库）
│   │   ├── qdrant_store.py              # Qdrant 实现（独立服务，未来）
│   │   └── checkpointer.py              # LangGraph 状态持久化适配
│   │
│   ├── callbacks/                       # 🆕 LangChain 回调处理器
│   │   ├── __init__.py
│   │   └── stream_callback.py           # 流式输出回调（转 WebSocket 消息）
│   │
│   ├── models/                          # 🆕 数据模型层（SQLAlchemy ORM）
│   │   ├── __init__.py
│   │   ├── base.py                      # 数据库引擎、会话工厂、基类
│   │   ├── session.py                   # Session 会话模型
│   │   └── message.py                   # Message 消息模型
│   │
│   ├── crud/                            # 🆕 数据访问层（CRUD）
│   │   ├── __init__.py
│   │   ├── base.py                      # 通用 BaseCRUD 基类
│   │   ├── session.py                   # SessionCRUD
│   │   └── message.py                   # MessageCRUD
│   │
│   ├── api/                             # ✅ 保持不变
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── session.py
│   │       ├── characters.py
│   │       ├── audio.py
│   │       ├── unity_ws.py
│   │       └── web_ws.py
│   │
│   ├── services/                        # ✏️ 简化
│   │   ├── __init__.py
│   │   ├── agent_service.py             # ✏️ 重构：只做协调，调用 Agent
│   │   ├── session_service.py           # ✅ 保持
│   │   ├── tts_service.py               # ✅ 保持
│   │   ├── tts_model_service.py         # ✅ 保持
│   │   ├── unity_service.py             # ✅ 保持
│   │   └── llm_service.py               # ❌ 删除（LangChain 接管）
│   │
│   ├── infrastructure/                  # ✏️ 部分调整
│   │   ├── __init__.py
│   │   ├── managers/
│   │   │   ├── __init__.py
│   │   │   ├── session_manager.py       # ✏️ 简化：只管会话元数据，历史由 LangGraph 管理
│   │   │   ├── character_registry.py    # ✅ 保持
│   │   │   ├── unity_connection.py      # ✅ 保持
│   │   │   └── web_connection.py        # ✅ 保持
│   │   └── processes/
│   │       ├── __init__.py
│   │       ├── tts_server.py            # ✅ 保持
│   │       └── unity_process.py         # ✅ 保持
│   │
│   ├── schemas/                         # ✅ 保持不变
│   │   ├── __init__.py
│   │   ├── character.py
│   │   ├── common.py
│   │   ├── session.py
│   │   ├── tts.py
│   │   ├── unity_protocol.py
│   │   ├── unity.py
│   │   └── web_protocol.py
│   │
│   ├── core/                            # ✏️ 新增配置项
│   │   ├── __init__.py
│   │   ├── config.py                    # ✏️ 新增 MEMORY_BACKEND, CHROMA_PERSIST_DIR 等
│   │   ├── constants.py
│   │   ├── container.py                 # ✏️ 新增 memory_store, checkpointer
│   │   ├── events.py
│   │   ├── exception_handler.py
│   │   ├── logger.py
│   │   ├── startup.py
│   │   └── static_files.py
│   │
│   ├── exceptions/                      # ✅ 保持不变
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── llm.py
│   │   ├── session.py
│   │   └── tts.py
│   │
│   ├── utils/                           # ✅ 保持不变
│   │   ├── __init__.py
│   │   ├── audio_utils.py
│   │   ├── path_utils.py
│   │   ├── prompts.py
│   │   └── text_buffer.py               # 继续用于 TTS 句子检测
│   │
│   ├── characters/                      # ✅ 保持不变
│   │   └── ...
│   │
│   └── main.py                          # ✅ 保持不变
│
├── data/                                # 🆕 数据持久化目录
│   ├── chroma/                          # Chroma 向量数据库存储
│   └── checkpoints/                     # LangGraph 状态检查点
│
├── pyproject.toml                       # ✏️ 新增依赖
├── run.py
└── .env.example                         # ✏️ 新增配置项
```

---

## 核心概念说明

### LangGraph State vs 运行阶段状态

这是两个不同的概念：

| 概念 | 类型 | 作用 | 例子 |
|------|------|------|------|
| **LangGraph State** | 数据容器 | 存储数据，在图节点间传递 | `messages`, `character_id`, `tool_results` |
| **运行阶段状态** | UI 通知 | 告诉前端当前执行到哪一步 | `thinking`, `calling_tool`, `idle` |

- **State** → 通过 `AgentState` 类定义
- **运行阶段** → 通过 `astream_events()` 事件流获取，转换成 WebSocket 消息发给前端

### LangGraph 流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Agent                          │
│                                                             │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐                │
│  │  Chat   │ ─► │  Router  │ ─► │ Respond │                │
│  │  Node   │    │ (条件边)  │    │  Node   │                │
│  └─────────┘    └──────────┘    └─────────┘                │
│       │              │               │                      │
│       │         ┌────▼────┐          │                      │
│       │         │  Tools  │          │                      │
│       │         │  Node   │──────────┘                      │
│       │         └─────────┘                                 │
│       └──────────────┴───────────────┘                      │
│                      │                                      │
│              ┌───────▼───────┐                              │
│              │  Agent State  │ ◄─── Checkpointer (持久化)   │
│              │  (messages)   │                              │
│              └───────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

**执行流程**：
1. 用户消息进入 → Chat Node 调用 LLM
2. LLM 决定是否需要工具 → Router 判断
3. 需要工具 → Tools Node 执行 → 返回 Chat Node 继续推理
4. 不需要工具 → Respond Node → 结束

---

## 模块职责说明

### agents/ 目录

| 文件 | 职责 |
|------|------|
| `state.py` | 定义 `AgentState`，继承 `MessagesState`，添加 `character_id` 等字段 |
| `graph.py` | 构建 LangGraph 图，定义节点和边，编译 Agent |
| `nodes.py` | 实现图节点：`chat_node`（调用 LLM）、`respond_node`（后处理） |
| `tools/__init__.py` | 导出 `get_all_tools()` 函数 |
| `tools/*.py` | 各个工具的实现（使用 `@tool` 装饰器） |

### memory/ 目录

| 文件 | 职责 |
|------|------|
| `base.py` | 定义 `MemoryStore` 抽象接口：`save_memory()`, `retrieve_relevant()` |
| `chroma_store.py` | Chroma 嵌入式实现，数据存本地文件 |
| `qdrant_store.py` | Qdrant 实现（未来，需要独立服务） |
| `checkpointer.py` | LangGraph Checkpointer 适配，用于会话状态持久化 |

### callbacks/ 目录

| 文件 | 职责 |
|------|------|
| `stream_callback.py` | LangChain `AsyncCallbackHandler`，将 LLM 事件转换为 WebSocket 消息 |

### models/ 目录（数据模型层）

| 文件 | 职责 |
|------|------|
| `base.py` | SQLAlchemy 引擎、异步会话工厂、`Base` 基类、`init_db()`/`close_db()` |
| `session.py` | `Session` 模型：会话元数据（id, character_id, title, language, timestamps） |
| `message.py` | `Message` 模型：消息记录（session_id, role, content, tool 相关字段） |

### crud/ 目录（数据访问层）

| 文件 | 职责 |
|------|------|
| `base.py` | 通用 `BaseCRUD` 基类，提供 CRUD 模板方法 |
| `session.py` | `SessionCRUD`：创建、查询、更新活跃时间、软删除、按角色分组 |
| `message.py` | `MessageCRUD`：添加消息、获取历史、滑动窗口、转 LangChain 格式 |

### services/agent_service.py（重构后）

**重构前职责**：消息处理 + LLM 调用 + 流式控制 + TTS 调度

**重构后职责**：
1. 验证输入
2. 获取会话信息
3. 调用 LangGraph Agent
4. 转发事件流到 WebSocket + TTS

### infrastructure/managers/session_manager.py（简化后）

**移除**：
- `ChatSession.history` 管理（由 LangGraph Checkpointer 接管）

**保留**：
- 会话元数据管理（session_id, character_id, created_at）
- 两级排序结构（通讯录功能）
- 音频队列（TTS 流式播放）

---

## 迁移路径

### Phase 1: 基础设施准备 ✅

- [x] 更新 `pyproject.toml` 添加依赖
- [x] 创建新目录：`agents/`, `memory/`, `callbacks/`
- [x] 更新 `config.py` 添加新配置项
- [x] 创建 `data/` 目录结构

**新增依赖**（pyproject.toml）:
```toml
# LangChain / LangGraph
langchain = ">=0.3.0"
langchain-openai = ">=0.3.0"
langgraph = ">=0.2.0"
langgraph-checkpoint-sqlite = ">=2.0.0"
langgraph-checkpoint-postgres = ">=2.0.0"

# Vector Database
chromadb = ">=0.5.0"

# Database
sqlalchemy[asyncio] = ">=2.0.0"
asyncpg = ">=0.30.0"
alembic = ">=1.14.0"
```

**新增配置项**（.env.example）:
```env
# Memory (向量数据库)
MEMORY_BACKEND=chroma
CHROMA_PERSIST_DIR=./data/chroma

# LangGraph Checkpoint (会话状态持久化)
CHECKPOINT_BACKEND=postgres
CHECKPOINT_DB_PATH=./data/checkpoints/langgraph.db

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/galatea
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/galatea
```

### Phase 2: Agent 核心 ✅

- [x] 实现 `agents/state.py` - AgentState 定义
- [x] 实现 `agents/nodes.py` - chat_node, respond_node
- [x] 实现 `agents/graph.py` - Agent 图构建（先不含工具）
- [x] 实现 `agents/__init__.py` - 导出 chat_agent
- [ ] 基础测试：确保对话流程正常

### Phase 3: 工具系统 ✅

- [x] 实现 `agents/tools/__init__.py` - get_all_tools()
- [ ] 实现第一个工具（如搜索）- 待添加
- [x] 更新 `agents/graph.py` - 添加工具节点和条件边
- [ ] 测试工具调用流程

### Phase 4: 输出管道重构 ✅

- [x] 实现 `callbacks/stream_callback.py` - LangChain 回调处理器
- [x] 重构 `services/agent_service.py` - 使用 astream_events
- [ ] 测试流式输出 + TTS

### Phase 5: 状态持久化 ✅

- [x] 实现 `memory/checkpointer.py` - Checkpointer 适配
- [x] 更新 `core/container.py` - 创建 checkpointer 实例
- [x] 更新 `agents/graph.py` - 使用持久化 checkpointer
- [ ] 简化 `session_manager.py` - 移除 history 管理（保留用于兼容）
- [ ] 测试：服务重启后会话恢复

### Phase 6: 向量记忆 ✅

- [x] 实现 `memory/base.py` - MemoryStore 接口
- [x] 实现 `memory/chroma_store.py` - Chroma 实现
- [x] 更新 `core/container.py` - 创建 memory_store 实例
- [ ] 在 Agent 中集成记忆检索（可选：在 chat_node 中检索相关记忆）
- [ ] 实现记忆提取逻辑（可选：在 respond_node 中提取对话要点）

### Phase 7: 清理 ✅

- [x] 删除 `services/llm_service.py`
- [ ] 清理 `session_manager.py` 中不再需要的代码（保留用于兼容）
- [x] 更新导入路径
- [ ] 完整测试

### Phase 8: 数据库层 ✅

- [x] 更新 `pyproject.toml` 添加 SQLAlchemy、asyncpg、alembic 依赖
- [x] 更新 `config.py` 添加 DATABASE_URL 配置
- [x] 实现 `models/base.py` - 数据库引擎和基类
- [x] 实现 `models/session.py` - Session 模型
- [x] 实现 `models/message.py` - Message 模型
- [x] 实现 `crud/base.py` - 通用 BaseCRUD 基类
- [x] 实现 `crud/session.py` - SessionCRUD
- [x] 实现 `crud/message.py` - MessageCRUD
- [x] 更新 `events.py` - 添加数据库初始化和关闭
- [x] 更新 `deps.py` - 添加数据库会话依赖
- [x] 更新 `checkpointer.py` - 添加 PostgreSQL 支持

---

## 部署方案

### Docker Compose

```yaml
version: "3.8"

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: galatea
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Galatea Server
  galatea-server:
    build:
      context: ./galatea_server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/galatea
      - DATABASE_URL_SYNC=postgresql://postgres:postgres@postgres:5432/galatea
      - MEMORY_BACKEND=chroma
      - CHROMA_PERSIST_DIR=/app/data/chroma
      - CHECKPOINT_BACKEND=postgres
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

### 数据目录

```
data/
├── chroma/              # Chroma 向量数据库（嵌入式）
└── checkpoints/         # LangGraph 状态检查点
    └── langgraph.db     # SQLite 存储
```

### Checkpointer 选择

| 类型 | 适用场景 |
|------|----------|
| `MemorySaver` | 开发测试，重启丢失 |
| `SqliteSaver` | 单机部署，持久化 |
| `PostgresSaver` | 多实例部署 |

### 向量数据库选择

| 方案 | 部署难度 | 适用场景 |
|------|----------|----------|
| Chroma (嵌入式) | ⭐ 最简单 | 单机部署，数据量不大 |
| Qdrant (Docker) | ⭐⭐⭐ | 需要更好性能 |
| Milvus | ⭐⭐⭐⭐ | 大规模生产 |

---

## 兼容性说明

- ✅ WebSocket 消息格式不变，前端无需修改
- ✅ REST API 接口不变
- ✅ 内部实现替换，外部接口兼容

---

## 参考资源

- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Chroma 文档](https://docs.trychroma.com/)

---

*文档创建时间: 2026-01-26*

# 数据库配置指南

本文档介绍如何配置 Galatea 项目所需的数据库服务。

## 目录

1. [概述](#概述)
2. [安装 Docker](#安装-docker)
3. [PostgreSQL 配置](#postgresql-配置)
4. [Chroma 向量数据库](#chroma-向量数据库)
5. [表结构说明](#表结构说明)
6. [常见问题](#常见问题)

---

## 概述

Galatea 使用以下数据存储：

| 数据库 | 用途 | 部署方式 |
|--------|------|----------|
| **PostgreSQL** | 会话元数据、消息历史、LangGraph 状态 | Docker 容器 |
| **Chroma** | 向量记忆（语义搜索） | 嵌入式（无需 Docker） |

### 为什么选择这个组合？

- **PostgreSQL**：成熟稳定，支持复杂查询，适合结构化数据
- **Chroma 嵌入式**：零配置，数据存本地文件，部署简单

---

## 安装 Docker

### Windows

1. **下载 Docker Desktop**
   
   访问 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 下载安装程序。

2. **系统要求**
   - Windows 10/11 64-bit
   - 启用 WSL 2（推荐）或 Hyper-V
   - 至少 4GB 内存

3. **安装步骤**
   - 运行安装程序
   - 勾选 "Use WSL 2 instead of Hyper-V"（推荐）
   - 完成安装后重启电脑

4. **验证安装**
   ```powershell
   docker --version
   docker compose version
   ```

### 启用 WSL 2（如果没有）

以管理员身份运行 PowerShell：
```powershell
# 启用 WSL
wsl --install

# 设置默认版本为 WSL 2
wsl --set-default-version 2
```

---

## PostgreSQL 配置

### 方式一：使用 Docker Compose（推荐）

在项目根目录创建或使用以下 `docker-compose.yml`：

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    container_name: galatea-postgres
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

volumes:
  postgres_data:
```

启动数据库：
```powershell
# 在项目根目录
docker compose up -d postgres

# 查看状态
docker compose ps

# 查看日志
docker compose logs postgres
```

### 方式二：单独运行 Docker 命令

```powershell
docker run -d `
  --name galatea-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=galatea `
  -p 5432:5432 `
  -v galatea_postgres_data:/var/lib/postgresql/data `
  postgres:16-alpine
```

### 连接配置

在 `.env` 文件中配置连接字符串：

```env
# 本地开发（Docker 运行在本机）
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/galatea
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/galatea

# LangGraph Checkpointer 也使用 PostgreSQL
CHECKPOINT_BACKEND=postgres
```

### 连接字符串格式

```
postgresql+asyncpg://[用户名]:[密码]@[主机]:[端口]/[数据库名]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 用户名 | `postgres` | PostgreSQL 用户 |
| 密码 | `postgres` | PostgreSQL 密码 |
| 主机 | `localhost` | 数据库服务器地址 |
| 端口 | `5432` | PostgreSQL 默认端口 |
| 数据库名 | `galatea` | 项目数据库 |

### 测试连接

```powershell
# 进入 PostgreSQL 容器
docker exec -it galatea-postgres psql -U postgres -d galatea

# 在 psql 中查看表
\dt

# 退出
\q
```

---

## Chroma 向量数据库

### 嵌入式模式（默认，无需 Docker）

当前配置使用嵌入式模式，Chroma 作为 Python 库直接运行，数据存储在本地文件。

```env
MEMORY_BACKEND=chroma
CHROMA_PERSIST_DIR=./data/chroma
```

数据存储位置：
```
galatea_server/
└── data/
    └── chroma/           # Chroma 数据目录
        ├── chroma.sqlite3
        └── ...
```

**优点**：
- 零配置，开箱即用
- 不需要额外的 Docker 容器
- 数据持久化到本地文件

### 独立服务模式（可选，未来扩展）

如果需要更高性能或多实例共享，可以使用 Docker 运行 Chroma 服务器：

```yaml
# 添加到 docker-compose.yml
services:
  chroma:
    image: chromadb/chroma:latest
    container_name: galatea-chroma
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    restart: unless-stopped

volumes:
  chroma_data:
```

然后修改代码使用 HTTP 客户端连接（需要修改 `chroma_store.py`）。

---

## 表结构说明

### 自动创建表

应用启动时会自动创建所有表（通过 SQLAlchemy）。无需手动执行 SQL。

```python
# app/core/events.py
async def lifespan(app: FastAPI):
    await init_db()  # 自动创建表
```

### Session 表

存储会话元数据。

```sql
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,           -- UUID 会话 ID
    character_id VARCHAR(50) NOT NULL,    -- 角色 ID
    title VARCHAR(200),                   -- 会话标题（可选）
    language VARCHAR(10) DEFAULT 'zh',    -- 语言
    enable_audio BOOLEAN DEFAULT TRUE,    -- 是否启用音频
    created_at TIMESTAMP NOT NULL,        -- 创建时间
    last_active TIMESTAMP NOT NULL,       -- 最后活跃时间
    is_deleted BOOLEAN DEFAULT FALSE      -- 软删除标记
);

-- 索引
CREATE INDEX ix_sessions_character_id ON sessions(character_id);
CREATE INDEX ix_sessions_is_deleted ON sessions(is_deleted);
```

### Message 表

存储对话消息历史。

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,                -- 自增 ID
    session_id VARCHAR(36) NOT NULL,      -- 关联会话
    role VARCHAR(20) NOT NULL,            -- 角色：system/user/assistant/tool
    content TEXT NOT NULL,                -- 消息内容
    message_id VARCHAR(36),               -- 前端消息 ID（可选）
    tool_name VARCHAR(100),               -- 工具名称（可选）
    tool_call_id VARCHAR(50),             -- 工具调用 ID（可选）
    created_at TIMESTAMP NOT NULL,        -- 创建时间
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX ix_messages_session_id ON messages(session_id);
CREATE INDEX ix_messages_created_at ON messages(created_at);
```

### LangGraph Checkpoint 表

由 `langgraph-checkpoint-postgres` 自动创建和管理，用于存储 Agent 状态。

```sql
-- 这些表由 LangGraph 自动创建，无需手动管理
-- checkpoints
-- checkpoint_writes
-- checkpoint_blobs
```

### ER 图

```
┌─────────────────────┐       ┌─────────────────────┐
│      sessions       │       │      messages       │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │◄──────│ session_id (FK)     │
│ character_id        │       │ id (PK)             │
│ title               │       │ role                │
│ language            │       │ content             │
│ enable_audio        │       │ message_id          │
│ created_at          │       │ tool_name           │
│ last_active         │       │ tool_call_id        │
│ is_deleted          │       │ created_at          │
└─────────────────────┘       └─────────────────────┘
         1                              N
```

---

## 完整 docker-compose.yml

项目根目录的完整配置：

```yaml
version: "3.8"

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:16-alpine
    container_name: galatea-postgres
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

  # Galatea Server（可选，也可以本地运行）
  # galatea-server:
  #   build:
  #     context: ./galatea_server
  #     dockerfile: Dockerfile
  #   ports:
  #     - "8000:8000"
  #   volumes:
  #     - ./galatea_server/data:/app/data
  #   environment:
  #     - LLM_API_KEY=${LLM_API_KEY}
  #     - LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}
  #     - LLM_BASE_URL=${LLM_BASE_URL}
  #     - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/galatea
  #     - MEMORY_BACKEND=chroma
  #     - CHECKPOINT_BACKEND=postgres
  #   depends_on:
  #     postgres:
  #       condition: service_healthy
  #   restart: unless-stopped

volumes:
  postgres_data:
```

---

## 快速开始

### 1. 安装 Docker Desktop

下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)。

### 2. 启动 PostgreSQL

```powershell
cd D:\SilverWolfSandbox\ai_Galatea
docker compose up -d postgres
```

### 3. 配置环境变量

复制并编辑 `.env` 文件：

```powershell
cd galatea_server
copy .env.example .env
```

编辑 `.env`，确保数据库配置正确：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/galatea
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/galatea
CHECKPOINT_BACKEND=postgres
MEMORY_BACKEND=chroma
```

### 4. 安装依赖

```powershell
cd galatea_server
uv sync
```

### 5. 启动应用

```powershell
uv run python run.py
```

应用启动时会自动创建数据库表。

---

## 常见问题

### Q: Docker Desktop 启动失败

**A**: 确保 WSL 2 已正确安装：
```powershell
wsl --status
```
如果未安装，运行 `wsl --install` 并重启。

### Q: 端口 5432 被占用

**A**: 修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "5433:5432"  # 使用 5433 端口
```
然后更新 `.env` 中的连接字符串：
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/galatea
```

### Q: 如何查看数据库内容？

**A**: 使用 psql 命令行：
```powershell
docker exec -it galatea-postgres psql -U postgres -d galatea
```

或安装 GUI 工具如 [pgAdmin](https://www.pgadmin.org/) 或 [DBeaver](https://dbeaver.io/)。

### Q: 如何备份数据库？

**A**: 
```powershell
# 备份
docker exec galatea-postgres pg_dump -U postgres galatea > backup.sql

# 恢复
docker exec -i galatea-postgres psql -U postgres galatea < backup.sql
```

### Q: 如何重置数据库？

**A**: 
```powershell
# 停止并删除容器和数据卷
docker compose down -v

# 重新启动（会创建新的空数据库）
docker compose up -d postgres
```

### Q: Chroma 数据在哪里？

**A**: 嵌入式模式下，数据存储在：
```
galatea_server/data/chroma/
```

可以直接删除这个目录来重置向量数据库。

---

## 网络配置说明

### 本地开发

所有服务运行在本机，使用 `localhost`：

```
┌─────────────────────────────────────────────┐
│               本地电脑                        │
│                                             │
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │ Galatea     │    │ Docker              │ │
│  │ Server      │───►│ PostgreSQL          │ │
│  │ (本地运行)   │    │ localhost:5432      │ │
│  └─────────────┘    └─────────────────────┘ │
│         │                                   │
│         ▼                                   │
│  ┌─────────────┐                            │
│  │ Chroma      │                            │
│  │ (嵌入式)     │                            │
│  │ ./data/chroma                            │
│  └─────────────┘                            │
└─────────────────────────────────────────────┘
```

### Docker Compose 网络

当所有服务都在 Docker 中运行时，使用服务名作为主机名：

```
┌─────────────────────────────────────────────┐
│          Docker Network (default)           │
│                                             │
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │ galatea-    │    │ postgres            │ │
│  │ server      │───►│ (服务名作为主机名)    │ │
│  │             │    │ postgres:5432       │ │
│  └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────┘
```

配置差异：

| 场景 | DATABASE_URL 主机部分 |
|------|----------------------|
| 本地开发 | `localhost:5432` |
| Docker Compose 内部 | `postgres:5432`（服务名） |

---

*文档创建时间: 2026-01-26*

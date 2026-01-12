# Galatea AI Chat System

[English](#english) | [中文](#中文)

---

<a name="english"></a>

## English

### Overview

**Galatea** is an intelligent chat system that integrates AI conversation, real-time 3D character visualization, and text-to-speech capabilities. It provides users with an immersive interactive experience through multi-language support and Unity-rendered character animations.

### Key Features

- **AI-Powered Conversations**: Context-aware dialogue powered by advanced language models
- **3D Character Visualization**: Real-time character rendering and animation in Unity
- **Text-to-Speech (TTS)**: Natural voice synthesis using GPT-SoVITS
- **Multi-language Support**: Seamless switching between Chinese and English
- **Pet Mode**: Minimalist floating window for unobtrusive interaction
- **Hot Character Swapping**: Switch between characters without restarting Unity
- **Session Management**: Organize conversations by character

---

### Architecture

Galatea uses a **three-tier architecture** with real-time communication:

```
┌─────────────────┐         WebSocket          ┌─────────────────┐
│                 │◄──────────────────────────►│                 │
│  Galatea Client │         REST API           │ Galatea Server  │
│   (Electron +   │◄──────────────────────────►│   (FastAPI)     │
│      React)     │                            │                 │
└─────────────────┘                            └────────┬────────┘
                                                        │
                                                        │ WebSocket
                                                        │
                                               ┌────────▼────────┐
                                               │                 │
                                               │  Galatea Unity  │
                                               │  (Unity 3D)     │
                                               │                 │
                                               └─────────────────┘
```

#### Component Details

1. **Galatea Client** (Frontend)
   - **Technology**: Electron + React + TypeScript
   - **Responsibilities**:
     - User interface and interaction
     - Session and contact management
     - Real-time message display
     - Language switching
     - Unity lifecycle control (launch/shutdown)

2. **Galatea Server** (Backend)
   - **Technology**: FastAPI + Python
   - **Responsibilities**:
     - AI conversation orchestration
     - Character configuration management
     - Session state management
     - TTS audio generation
     - WebSocket hub for Client ↔ Unity communication

3. **Galatea Unity** (3D Visualization)
   - **Technology**: Unity 3D + C#
   - **Responsibilities**:
     - Character model rendering
     - Idle animations and expressions
     - Lip-sync with audio playback
     - Real-time character switching

#### Communication Flow

1. **User sends message** → Client sends to Server via WebSocket
2. **Server processes** → Calls LLM API, generates response and audio
3. **Server broadcasts** → Sends text to Client, animation/audio instructions to Unity
4. **Unity renders** → Plays character animation and lip-synced speech
5. **Client displays** → Shows AI response in chat interface

---

### Deployment & Installation

#### Prerequisites

- **Operating System**: Windows 10 or higher
- **Python**: 3.13 or higher
- **Node.js**: 16.x or higher
- **uv**: Python package manager (optional but recommended, `pip install uv`)
- **npm**: Node.js package manager (comes with Node.js)
- **GPT-SoVITS**: Running on `http://127.0.0.1:9880` (required for TTS feature, must be deployed locally)

#### For End Users (Recommended)

Download the pre-built package from [GitHub Releases](https://github.com/YOUR_USERNAME/ai_Galatea/releases) which includes all character data, models, and configuration files.

1. **Download and extract**
   ```bash
   # Download galatea-v1.0.0.zip from Releases
   unzip galatea-v1.0.0.zip
   cd galatea-v1.0.0
   ```

2. **Install dependencies (automated)**
   ```bash
   install.bat
   ```
   
   The script will automatically:
   - Check for Python and Node.js
   - Install Python dependencies using `uv` (or fallback to `pip`)
   - Install frontend dependencies using `npm`
   - Create `.env` template files

3. **Configure environment**
   ```bash
   # Edit server configuration
   cd galatea_server
   # Edit .env to add your API keys (OPENAI_API_KEY, etc.)
   ```

4. **Start the application**
   ```bash
   cd ..
   start.bat
   ```

5. **Access**
   - The Electron client will launch automatically
   - Server runs on `http://localhost:8000`
   - Unity client (if included) launches via the UI button

---

### Usage Guide

1. **Create a Session**
   - Click the "+" button in the contacts panel
   - Select a character to start a new conversation

2. **Chat**
   - Type messages in the input box
   - Press `Enter` to send (Shift+Enter for new line)
   - Toggle audio on/off using the speaker icon

3. **Launch Unity**
   - Click the Unity icon in the toolbar
   - The 3D character will appear in a separate window
   - Character will automatically sync with the active session

4. **Pet Mode**
   - Click the grid icon to enable compact pet mode
   - Minimize to a floating ball for unobtrusive desktop presence

---

### FutureRoadmap

#### Phase 1: Agent Architecture (Q2 2026)
- [ ] Implement **agentic character behavior**
  - Tool calling capabilities (web search, file access, etc.)
  - Memory management across sessions
  - Multi-step planning and reasoning
- [ ] Design modular agent framework for character extensibility

#### Phase 2: UI/UX Enhancements (Q2-Q3 2026)
- [ ] Optimize input area interactions
  - File attachment support
  - Rich text formatting
  - Voice input
- [ ] **TTS Service Compatibility**
  - Support network-based TTS API (e.g., Azure TTS, ElevenLabs)
  - Decouple from local GPT-SoVITS dependency

#### Phase 3: User Customization (Q3 2026)
- [ ] **Custom Character Import System**
  - Upload 3D models (currently supports PMX format only)
  - Define custom personas and prompts
  - Configure animation parameters and blend shapes
- [ ] Visual character editor

---

### License

This project is licensed under the [MIT License](LICENSE).

### Acknowledgments

- **GPT-SoVITS** for TTS capabilities
- **OVR Lip Sync** for lip-sync functionality
- **MMD4Mecanim** for PMX model import and animation support

---

<a name="中文"></a>

## 中文

### 项目简介

**Galatea** 是一个集成了 AI 对话、实时 3D 角色可视化和语音合成的智能聊天系统。通过多语言支持和 Unity 渲染的角色动画，为用户提供沉浸式的交互体验。

### 核心功能

- **AI 智能对话**：基于大语言模型的上下文感知对话
- **3D 角色可视化**：Unity 实时渲染角色动画
- **语音合成 (TTS)**：使用 GPT-SoVITS 的自然语音合成
- **多语言支持**：中英文无缝切换
- **桌宠模式**：极简悬浮窗，不影响其他工作
- **角色热切换**：无需重启 Unity 即可切换角色
- **会话管理**：按角色组织对话记录

---

### 系统架构

Galatea 采用 **三端实时通信架构**：

```
┌─────────────────┐         WebSocket          ┌─────────────────┐
│                 │◄──────────────────────────►│                 │
│  Galatea Client │         REST API           │ Galatea Server  │
│   (Electron +   │◄──────────────────────────►│   (FastAPI)     │
│      React)     │                            │                 │
└─────────────────┘                            └────────┬────────┘
                                                        │
                                                        │ WebSocket
                                                        │
                                               ┌────────▼────────┐
                                               │                 │
                                               │  Galatea Unity  │
                                               │  (Unity 3D)     │
                                               │                 │
                                               └─────────────────┘
```

#### 组件详解

1. **Galatea Client** (前端)
   - **技术栈**：Electron + React + TypeScript
   - **职责**：
     - 用户界面和交互逻辑
     - 会话和通讯录管理
     - 实时消息展示
     - 语言切换
     - Unity 生命周期控制（启动/关闭）

2. **Galatea Server** (后端)
   - **技术栈**：FastAPI + Python
   - **职责**：
     - AI 对话协调
     - 角色配置管理
     - 会话状态管理
     - TTS 音频生成
     - WebSocket 中转（Client ↔ Unity）

3. **Galatea Unity** (3D 可视化)
   - **技术栈**：Unity 3D + C#
   - **职责**：
     - 角色模型渲染
     - 待机动画和表情控制
     - 口型同步与音频播放
     - 实时角色切换

#### 通信流程

1. **用户发送消息** → Client 通过 WebSocket 发送至 Server
2. **Server 处理** → 调用 LLM API，生成回复和音频
3. **Server 广播** → 文本发送至 Client，动画/音频指令发送至 Unity
4. **Unity 渲染** → 播放角色动画和口型同步语音
5. **Client 展示** → 在聊天界面显示 AI 回复

---

### 部署与安装

#### 前置要求

- **操作系统**：Windows 10 或更高版本
- **Python**：3.13 或更高版本
- **Node.js**：16.x 或更高版本
- **uv**：Python 包管理器（可选但推荐，`pip install uv`）
- **npm**：Node.js 包管理器（随 Node.js 自带）
- **GPT-SoVITS**：运行在 `http://127.0.0.1:9880`（语音功能可以选，需依赖本地部署GPT-SoVIts）

#### 普通用户使用（推荐）

从 [GitHub Releases](https://github.com/YOUR_USERNAME/ai_Galatea/releases) 下载预构建安装包，其中包含所有角色数据、模型和配置文件。

1. **下载并解压**
   ```bash
   # 从 Releases 下载 galatea-v1.0.0.zip
   unzip galatea-v1.0.0.zip
   cd galatea-v1.0.0
   ```

2. **自动安装依赖**
   ```bash
   install.bat
   ```
   
   脚本会自动完成：
   - 检查 Python 和 Node.js
   - 使用 `uv` 安装 Python 依赖（如无 `uv` 则使用 `pip`）
   - 使用 `npm` 安装前端依赖
   - 创建 `.env` 模板文件

3. **配置环境**
   ```bash
   # 编辑服务端配置
   cd galatea_server
   # 编辑 .env 文件，添加 API 密钥（OPENAI_API_KEY 等）
   ```

4. **启动应用**
   ```bash
   cd ..
   start.bat
   ```

5. **访问**
   - Electron 客户端将自动启动
   - 服务器运行在 `http://localhost:8000`
   - Unity 客户端（如果包含）通过 UI 按钮启动

---

### 使用指南

1. **创建会话**
   - 点击通讯录面板中的 "+" 按钮
   - 选择一个角色开始新的对话

2. **聊天**
   - 在输入框中输入消息
   - 按 `Enter` 发送（Shift+Enter 换行）
   - 使用扬声器图标切换音频开关

3. **启动 Unity**
   - 点击工具栏中的 Unity 图标
   - 3D 角色将在独立窗口中显示
   - 角色会自动同步当前会话

4. **切换语言**
   - 点击右上角的 "Lang: En" 或 "Lang: 中"
   - 从下拉菜单中选择语言

5. **桌宠模式**
   - 点击网格图标启用紧凑桌宠模式
   - 最小化为悬浮球，不妨碍桌面使用

---

### 未来开发路线图

#### 阶段一：Agent 架构 (2026 Q2)
- [ ] 实现**角色 Agent 化**
  - 工具调用能力（网络搜索、文件访问等）
  - 跨会话记忆管理
  - 多步骤规划和推理
- [ ] 设计模块化 Agent 框架，提升角色可扩展性

#### 阶段二：前端交互优化 (2026 Q2-Q3)
- [ ] 优化输入区域交互
  - 文件附件支持
  - 富文本格式化
  - 语音输入
- [ ] **TTS 服务兼容性**
  - 支持网络 TTS API（如 Azure TTS、ElevenLabs）
  - 解除对本地 GPT-SoVITS 的依赖

#### 阶段三：用户自定义角色 (2026 Q3)
- [ ] **自定义角色导入系统**
  - 上传 3D 模型（目前仅支持 pmx 格式）
  - 定义自定义人物设定和提示词
  - 配置动作参数和 Blend Shape
- [ ] 可视化角色编辑器

---

### 许可证

本项目采用 [MIT 许可证](LICENSE)。

### 致谢

- **GPT-SoVITS** 提供 TTS 能力
- **OVR Lip Sync** 提供口型同步功能
- **MMD4Mecanim** 提供 PMX 模型导入和动画支持
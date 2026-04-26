# 刻甲 Carvor - AI 科研助手

<div align="center">

[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![React version](https://img.shields.io/badge/react-18.3.1-blue.svg)](https://react.dev/)

</div>

## 简介

刻甲（Carvor）是一款专注于科研工作流的AI助手，整合了论文跟踪、Idea锤炼、深度阅读、综述撰写、方法讨论、提示词生成、论文润色等全流程功能。

## 功能特性

- 📚 **论文库管理** - 自动搜索最新论文，语义检索，PDF深度阅读
- 💡 **Idea锤炼** - 与AI讨论研究想法，自动分析可行性和创新点
- 📝 **综述撰写** - AI辅助生成文献综述
- 🔬 **方法讨论** - 完善研究方法和实验设计
- 📌 **提示词生成** - 基于研究文档生成代码提示词
- ✏️ **论文润色** - AI辅助润色学术论文
- 📊 **科研时间线** - 自动按周组织论文，生成周报
- 🧠 **向量检索** - 本地向量索引，快速语义检索
- 📈 **技能进化** - AI持续学习用户偏好和研究习惯

## 技术架构

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: React + TypeScript + Ant Design + Vite
- **LLM**: 支持兼容OpenAI API的各类模型（如Moonshot、DeepSeek等）
- **向量库**: LlamaIndex + HuggingFace Embeddings (bge-small-zh-v1.5)

## Windows 本地部署

### 前置要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 部署步骤

#### 1. 克隆项目

```bash
git clone https://github.com/hherosoul/carvor.git
cd carvor
```

#### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 3. 构建前端

```bash
cd ../frontend
npm install
npm run build
```

#### 4. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
cd ..
start.bat
```

**方式二：手动启动**

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 5173
```

#### 5. 访问应用

在浏览器中打开：`http://localhost:5173`

## 配置说明

首次使用时，进入"设置"页面配置LLM API：

- `Base URL`: API服务地址（如 `https://api.moonshot.cn/v1`）
- `API Key`: 你的API密钥
- `Model`: 模型名称（如 `kimi-k2.6`）

配置完成后即可正常使用。

## 项目结构

```
carvor/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API路由
│   │   ├── core/            # 核心模块（配置、数据库、调度等）
│   │   ├── gateway/         # LLM网关
│   │   ├── models/          # 数据模型
│   │   ├── pipelines/       # 业务流程
│   │   ├── scenarios/       # 场景定义
│   │   └── services/        # 服务层（向量搜索等）
│   ├── config/              # 配置文件
│   ├── data/                # 数据文件
│   ├── models/              # 本地模型
│   └── skills/              # 技能文件
├── frontend/
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── hooks/           # 自定义hooks
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API服务
│   │   ├── stores/          # 状态管理
│   │   ├── styles/          # 样式
│   │   └── types/           # TypeScript类型
│   └── dist/                # 构建输出
└── docs/                    # 文档
```

## 开发指南

### 后端开发

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

前端开发模式默认会在 `http://localhost:5173` 启动，API请求会被代理到 `http://localhost:8000`。

## 常见问题

**Q: 后端启动后提示找不到模型？**

A: 首次使用时，向量搜索会自动从HuggingFace下载 `bge-small-zh-v1.5` 模型。下载失败可以手动下载到 `backend/models/bge-small-zh-v1.5/`。

**Q: 如何切换LLM模型？**

A: 在"设置"页面添加新的LLM提供商配置，然后点击"激活"切换。

**Q: 数据存储在哪里？**

A: 所有数据都存储在 `backend/data/` 目录下，包括SQLite数据库、向量索引、用户上传的PDF等。

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

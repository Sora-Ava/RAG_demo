# 企业 RAG 知识库 + 多工具 Agent —— 启动说明

## 一、快速启动（Docker，推荐）

```bash
# 1. 克隆 / 进入项目目录
cd rag_agent

# 2. 创建配置文件
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key 和 Base URL

# 3. 一键构建并启动（首次约 5-10 分钟，下载模型）
docker compose up --build

# 4. 访问接口文档
open http://localhost:8000/docs
```

> **注意**：首次启动会自动下载 `BAAI/bge-small-zh-v1.5` 模型（约 100 MB）。
> 网络受限时可提前手动下载并挂载到容器内。

---

## 二、本地开发启动（无 Docker）

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env               # 修改 OPENAI_API_KEY 等

# 4. 修改数据路径（本地开发使用相对路径）
# 在 .env 中：
#   CHROMA_PERSIST_DIR=./data/chroma
#   UPLOAD_DIR=./data/uploads

# 5. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 三、API 使用示例

### 上传文档
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/your/document.pdf"
```

### 多轮对话
```bash
# 第一轮
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "公司的请假制度是什么？"}'

# 第二轮（传入 session_id 延续上下文）
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "那病假呢？", "session_id": "上一步返回的session_id"}'

# 查询天气（自动调用天气工具）
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京今天天气怎么样？"}'
```

### 查看工具列表
```bash
curl http://localhost:8000/tools
```

### 清空知识库
```bash
curl -X DELETE http://localhost:8000/clear
```

---

## 四、LLM 配置参考

| 服务商 | OPENAI_BASE_URL | OPENAI_MODEL |
|--------|----------------|--------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo` / `gpt-4o` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` / `qwen-plus` |
| 文心一言 | `https://qianfan.baidubce.com/v2` | `ernie-4.0-8k` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3` / `qwen2` |

---

## 五、项目结构

```
rag_agent/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 统一配置（读取 .env）
│   ├── models.py            # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── upload.py        # POST /upload
│   │   ├── chat.py          # POST /chat
│   │   ├── tools.py         # GET  /tools
│   │   └── admin.py         # DELETE /clear
│   ├── agent/
│   │   ├── state.py         # LangGraph 状态定义
│   │   ├── nodes.py         # Agent/工具节点（含重试）
│   │   └── graph.py         # LangGraph 工作流编排
│   ├── tools/
│   │   ├── rag_tool.py      # RAG 检索工具
│   │   ├── weather_tool.py  # 天气查询工具
│   │   └── api_tool.py      # 通用 HTTP 工具
│   ├── rag/
│   │   ├── document_loader.py  # PDF/Word/TXT 解析
│   │   ├── chunker.py          # 文本分片
│   │   ├── embedder.py         # BGE-small 嵌入
│   │   └── vector_store.py     # Chroma 向量库
│   └── memory/
│       └── session.py       # 会话元数据管理
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── STARTUP.md
```

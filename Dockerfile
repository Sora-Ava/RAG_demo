# ──────────────────────────────────────────────────────────────────────────────
# 多阶段构建：构建期只装包，模型在容器首次启动时通过 ModelScope 下载
# ──────────────────────────────────────────────────────────────────────────────

# ── 阶段 1：依赖安装 ──────────────────────────────────────────────────────────
FROM docker.m.daocloud.io/library/python:3.11-slim AS builder

WORKDIR /build

# 切换 apt 源为阿里云
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 系统编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl build-essential git \
    && rm -rf /var/lib/apt/lists/*

# pip 走阿里云镜像，安装所有依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ \
    && pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/


# ── 阶段 2：运行镜像 ──────────────────────────────────────────────────────────
FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

# 切换 apt 源 + 安装 curl（健康检查用）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制已安装的 Python 包
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY app/ ./app/

# 创建数据目录 & 模型缓存目录
RUN mkdir -p /app/data/chroma /app/data/uploads /app/models

# 模型使用 ModelScope 下载（国内必通），缓存路径挂载为 volume 持久化
# 首次启动自动下载，之后直接读缓存，无需重复下载
ENV MODELSCOPE_CACHE=/app/models
ENV MODEL_NAME=BAAI/bge-small-zh-v1.5

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

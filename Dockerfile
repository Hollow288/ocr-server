# 基础镜像：官方 Python
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

ENV KMP_DUPLICATE_LIB_OK=TRUE \
    FLAGS_enable_mkldnn=0 \
    FLAGS_enable_onednn=0

# 设置工作目录
WORKDIR /app

# 安装系统依赖（paddle 运行必须）
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install --no-cache-dir poetry

# 先复制 poetry 文件（利用 Docker 缓存）
COPY pyproject.toml poetry.lock* /app/

# 安装 Python 依赖
RUN poetry install --no-root

# 再复制代码
COPY . /app

# 暴露端口
EXPOSE 8000

# 启动 FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

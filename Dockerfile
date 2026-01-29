# 降级到 3.10-slim，AI 兼容性最好
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# 针对 Paddle 的 CPU 优化设置，防止某些指令集报错
ENV KMP_DUPLICATE_LIB_OK=TRUE \
    FLAGS_enable_mkldnn=0 \
    FLAGS_enable_onednn=0

WORKDIR /app

# 安装必要的系统库 (libgl1 是 opencv 必须，libgomp1 是 paddle 必须)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libstdc++6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/

# 安装依赖
RUN poetry install --no-root

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
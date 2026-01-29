# 基础镜像
FROM python:3.13-slim

# 必须在 install 前设置
ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    KMP_DUPLICATE_LIB_OK=TRUE \
    FLAGS_enable_mkldnn=0 \
    FLAGS_enable_onednn=0

# 安装 Poetry
RUN pip install --upgrade pip \
    && pip install poetry

# 复制项目
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# 安装依赖（直接到系统 Python）
RUN poetry install --no-root

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

CMD ["python", "main.py"]

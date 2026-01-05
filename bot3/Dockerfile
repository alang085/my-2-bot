# 使用 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
# 使用 .dockerignore 控制排除的文件
COPY . .

# 创建数据目录（用于数据库文件）
# 注意：在 Zeabur 中，数据目录应该挂载为持久化存储卷
RUN mkdir -p /app/data

# 设置数据目录权限
RUN chmod -R 755 /app/data

# 设置工作目录为应用根目录
WORKDIR /app

# 暴露端口（如果需要健康检查）
# EXPOSE 8000

# 运行机器人
CMD ["python", "main.py"]


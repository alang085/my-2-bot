# Docker 镜像构建和推送指南

## 📋 方案概述

1. 本地构建 Docker 镜像
2. 推送到 Docker Registry（Docker Hub 或 GitLab Container Registry）
3. 在 Zeabur/Railway 等平台使用镜像部署

---

## 🐳 方案1：推送到 Docker Hub（推荐）

### 步骤1：注册 Docker Hub 账户

1. 访问：https://hub.docker.com
2. 注册/登录账户
3. 记住你的用户名（例如：`yourusername`）

### 步骤2：在本地构建 Docker 镜像

```bash
# 1. 确保在项目根目录
cd C:\Users\zhuanqian\Desktop\01_项目代码\loan005.bot

# 2. 构建镜像（替换 yourusername 为你的Docker Hub用户名）
docker build -t yourusername/loan-bot:latest .

# 或者指定版本号
docker build -t yourusername/loan-bot:v1.0.0 .
```

**说明**：
- `yourusername/loan-bot` 是镜像名称
- `latest` 或 `v1.0.0` 是标签（版本号）
- `.` 表示使用当前目录的 Dockerfile

### 步骤3：登录 Docker Hub

```bash
docker login
# 输入你的 Docker Hub 用户名和密码
```

### 步骤4：推送镜像到 Docker Hub

```bash
# 推送 latest 标签
docker push yourusername/loan-bot:latest

# 或者推送特定版本
docker push yourusername/loan-bot:v1.0.0
```

### 步骤5：在 Zeabur 使用镜像部署

1. 在 Zeabur 创建新项目
2. 选择 "Deploy from Docker image" 或类似选项
3. 输入镜像地址：`yourusername/loan-bot:latest`
4. 配置环境变量和 Volume

---

## 🔵 方案2：推送到 GitLab Container Registry

### 步骤1：获取 GitLab Registry 地址

你的 GitLab 仓库：`alang085-group/my-bot1`

Registry 地址格式：`registry.gitlab.com/alang085-group/my-bot1`

### 步骤2：登录 GitLab Container Registry

```bash
# 使用 GitLab Personal Access Token 登录
docker login registry.gitlab.com -u <你的GitLab用户名> -p <你的Personal Access Token>
```

**创建 Personal Access Token**：
1. GitLab → 右上角头像 → Preferences → Access Tokens
2. Token name: `docker-registry`
3. Scopes: 勾选 `write_registry` 和 `read_registry`
4. 创建并复制 Token

### 步骤3：构建并标记镜像

```bash
# 构建镜像，使用 GitLab Registry 地址
docker build -t registry.gitlab.com/alang085-group/my-bot1:latest .
```

### 步骤4：推送镜像

```bash
docker push registry.gitlab.com/alang085-group/my-bot1:latest
```

### 步骤5：在平台使用镜像

使用镜像地址：`registry.gitlab.com/alang085-group/my-bot1:latest`

---

## 🛠️ 详细操作步骤（Docker Hub 示例）

### 1. 检查 Dockerfile

确保项目根目录有 `Dockerfile` 文件：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc tzdata && \
    ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
RUN mkdir -p /data
ENV DATA_DIR=/data
CMD ["python", "main.py"]
```

### 2. 构建镜像

```bash
# Windows PowerShell
docker build -t yourusername/loan-bot:latest .
```

**构建过程**：
- 会下载基础镜像（python:3.11-slim）
- 安装依赖
- 复制代码
- 可能需要几分钟时间

### 3. 测试镜像（可选）

```bash
# 运行镜像测试（使用环境变量）
docker run --rm \
  -e BOT_TOKEN="你的Token" \
  -e ADMIN_USER_IDS="你的用户ID" \
  -e DATA_DIR=/data \
  -v "$(pwd)/data:/data" \
  yourusername/loan-bot:latest
```

### 4. 登录并推送

```bash
# 登录 Docker Hub
docker login

# 推送镜像
docker push yourusername/loan-bot:latest
```

---

## 📝 在 Zeabur 使用 Docker 镜像

### 如果 Zeabur 支持 Docker 镜像部署：

1. **创建新项目**
   - New Project → Deploy from Docker image
   - 或选择 Custom Docker

2. **输入镜像地址**
   ```
   # Docker Hub
   yourusername/loan-bot:latest
   
   # GitLab Registry
   registry.gitlab.com/alang085-group/my-bot1:latest
   ```

3. **配置环境变量**
   ```
   BOT_TOKEN=你的机器人Token
   ADMIN_USER_IDS=你的用户ID
   DATA_DIR=/data
   ```

4. **配置 Volume**
   - Mount Path: `/data`

---

## ⚙️ 优化构建（可选）

### 使用 .dockerignore

确保 `.dockerignore` 文件存在，排除不必要的文件：

```
__pycache__
*.pyc
*.db
.git
.env
*.log
```

### 多阶段构建（如果镜像太大）

可以优化 Dockerfile 减少镜像大小。

---

## 🔍 常见问题

### 问题1：docker build 失败

**检查**：
- Docker 是否已安装并运行
- Dockerfile 是否存在
- 网络连接是否正常

### 问题2：docker push 权限被拒绝

**解决**：
- 确保已登录：`docker login`
- 检查用户名是否正确
- 确保有推送权限

### 问题3：镜像太大

**优化**：
- 使用 .dockerignore 排除文件
- 使用多阶段构建
- 清理构建缓存

---

## 🚀 快速开始

让我帮你构建和推送镜像，你需要：

1. **选择 Registry**：
   - Docker Hub（推荐，更通用）
   - GitLab Container Registry（如果你更喜欢用GitLab）

2. **告诉我你的账户信息**：
   - Docker Hub 用户名（如果选择Docker Hub）
   - 或 GitLab Personal Access Token（如果选择GitLab）

你想使用哪个 Registry？我可以帮你构建和推送。


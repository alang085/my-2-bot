# 部署指南

**版本**: 1.0  
**创建日期**: 2026-01-05  
**最后更新**: 2026-01-05

---

## 📋 概述

本文档提供 `bot3` Telegram 机器人的完整部署指南，包括本地部署、Docker 部署和云平台部署。

---

## 🚀 部署方式

### 方式 1: 本地部署

#### 前置要求

- Python 3.9 或更高版本
- pip 包管理器

#### 步骤

1. **克隆或下载项目**
   ```bash
   cd /path/to/bot3
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   
   创建 `.env` 文件或设置环境变量：
   ```bash
   export BOT_TOKEN="your_bot_token_here"
   export ADMIN_USER_IDS="123456789,987654321"
   ```

   或创建 `user_config.py`（仅用于本地开发）：
   ```python
   BOT_TOKEN = "your_bot_token_here"
   ADMIN_USER_IDS = "123456789,987654321"
   ```

4. **运行机器人**
   ```bash
   python main.py
   ```

---

### 方式 2: Docker 部署

#### 前置要求

- Docker 和 Docker Compose

#### 步骤

1. **准备环境变量文件**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入 BOT_TOKEN 和 ADMIN_USER_IDS
   ```

2. **构建并启动容器**
   ```bash
   docker-compose up -d
   ```

3. **查看日志**
   ```bash
   docker-compose logs -f
   ```

4. **停止容器**
   ```bash
   docker-compose down
   ```

#### 手动 Docker 命令

```bash
# 构建镜像
docker build -t telegram-bot:latest .

# 运行容器
docker run -d \
  --name telegram-bot \
  --restart unless-stopped \
  -e BOT_TOKEN="your_bot_token" \
  -e ADMIN_USER_IDS="123456789,987654321" \
  -v $(pwd)/data:/app/data \
  telegram-bot:latest

# 查看日志
docker logs -f telegram-bot
```

---

### 方式 3: 云平台部署

#### Zeabur 部署

1. **连接 GitHub 仓库**
   - 在 Zeabur 中创建新项目
   - 连接到 GitHub 仓库

2. **配置环境变量**
   - `BOT_TOKEN`: 您的 Telegram Bot Token
   - `ADMIN_USER_IDS`: 管理员用户ID（逗号分隔，无空格）
   - `DATA_DIR`: `/app/data`（可选，Zeabur 会自动设置）

3. **部署**
   - Zeabur 会自动检测 Dockerfile 并构建
   - 部署完成后，机器人会自动启动

#### Railway 部署

1. **连接 GitHub 仓库**
   - 在 Railway 中创建新项目
   - 连接到 GitHub 仓库

2. **配置环境变量**
   - 在 Railway 项目设置中添加环境变量
   - `BOT_TOKEN`: 您的 Telegram Bot Token
   - `ADMIN_USER_IDS`: 管理员用户ID

3. **部署**
   - Railway 会自动检测并部署
   - 使用 Dockerfile 或直接运行 Python

#### Heroku 部署

1. **安装 Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```

2. **登录 Heroku**
   ```bash
   heroku login
   ```

3. **创建应用**
   ```bash
   heroku create your-bot-name
   ```

4. **设置环境变量**
   ```bash
   heroku config:set BOT_TOKEN="your_bot_token"
   heroku config:set ADMIN_USER_IDS="123456789,987654321"
   ```

5. **部署**
   ```bash
   git push heroku main
   ```

6. **查看日志**
   ```bash
   heroku logs --tail
   ```

---

## 🔧 配置说明

### 必需环境变量

- **BOT_TOKEN**: Telegram Bot Token（从 @BotFather 获取）
- **ADMIN_USER_IDS**: 管理员用户ID列表（逗号分隔，无空格）

### 可选环境变量

- **DATA_DIR**: 数据目录路径（默认：项目根目录）
- **LOG_LEVEL**: 日志级别（默认：INFO）
- **DEBUG**: 调试模式（0=关闭，1=开启）

---

## 📊 数据持久化

### Docker 部署

使用 Docker Compose 时，数据会自动持久化到 `./data` 目录：

```yaml
volumes:
  - ./data:/app/data
```

### 云平台部署

- **Zeabur**: 使用持久化存储卷
- **Railway**: 使用持久化存储卷
- **Heroku**: 使用 Heroku Postgres（需要迁移到 PostgreSQL）或使用外部存储

---

## 🔍 监控和日志

### 查看日志

**本地部署**:
```bash
tail -f bot_runtime.log
```

**Docker 部署**:
```bash
docker-compose logs -f
```

**云平台**:
- Zeabur: 在项目页面查看日志
- Railway: 在项目页面查看日志
- Heroku: `heroku logs --tail`

### 健康检查

机器人会自动记录启动和运行状态。如果机器人停止响应，检查：

1. 日志文件中的错误信息
2. 网络连接
3. Telegram API 状态
4. 数据库文件权限

---

## 🛠️ 故障排除

### 问题 1: Conflict 错误

**错误信息**: `Conflict: terminated by other getUpdates request`

**原因**: 有多个机器人实例在运行

**解决方案**:
1. 停止所有其他实例
2. 等待 30-60 秒
3. 重新启动

### 问题 2: 数据库权限错误

**错误信息**: `Permission denied` 或 `Read-only file system`

**解决方案**:
1. 检查数据目录权限
2. 确保容器有写入权限
3. 检查挂载卷配置

### 问题 3: 依赖安装失败

**解决方案**:
1. 更新 pip: `pip install --upgrade pip`
2. 使用虚拟环境
3. 检查 Python 版本（需要 3.9+）

---

## 🔐 安全建议

1. **保护敏感信息**
   - 永远不要将 `BOT_TOKEN` 提交到 Git
   - 使用环境变量或密钥管理服务
   - 确保 `.env` 和 `user_config.py` 在 `.gitignore` 中

2. **定期更新**
   - 定期更新依赖包
   - 关注安全公告
   - 使用 `pip list --outdated` 检查过时包

3. **备份数据**
   - 定期备份数据库文件
   - 使用版本控制管理代码
   - 保留部署日志

---

## 📚 相关文档

- [启动指南](./STARTUP_GUIDE.md)
- [使用指南](./BOT_USAGE_GUIDE.md)
- [故障排除](./STARTUP_CONFLICT_FIX.md)
- [CI/CD 指南](./CICD_GUIDE.md)

---

## 🎯 部署检查清单

- [ ] 已安装所有依赖
- [ ] 已配置环境变量（BOT_TOKEN, ADMIN_USER_IDS）
- [ ] 已测试本地运行
- [ ] 已创建数据目录（如需要）
- [ ] 已配置日志记录
- [ ] 已设置自动重启（如需要）
- [ ] 已配置数据备份
- [ ] 已测试机器人功能

---

**维护者**: 开发团队  
**最后更新**: 2026-01-05


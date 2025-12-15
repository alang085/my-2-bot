# Zeabur 部署指南

## 📋 部署前检查清单

- [x] `requirements.txt` - Python 依赖已配置
- [x] `Procfile` - 启动命令已配置
- [x] `.gitignore` - 敏感文件已排除
- [x] `zeabur.json` - Zeabur 配置已创建
- [ ] 环境变量已准备（BOT_TOKEN, ADMIN_USER_IDS）
- [ ] Git 仓库已创建并推送代码

## 🚀 快速部署步骤

### 1. 准备 Git 仓库

```bash
# 初始化 Git（如果还没有）
git init
git add .
git commit -m "Initial commit for Zeabur deployment"

# 推送到 GitHub/GitLab
git remote add origin <你的仓库地址>
git push -u origin main
```

### 2. 在 Zeabur 部署

1. 访问 [Zeabur Dashboard](https://dash.zeabur.com)
2. 点击 **"New Project"**
3. 选择 **"Import from Git"**
4. 连接你的 Git 仓库（GitHub/GitLab）
5. 选择仓库和分支
6. 选择根目录为项目根目录

### 3. 配置持久化存储（重要！）

**添加 Volume：**
1. 在 Zeabur 项目设置中找到 "Volumes" 或 "Storage"
2. 添加 Volume：
   - **Mount Path**: `/data`
   - **Size**: 1GB（可根据需要调整）

### 4. 配置环境变量

在 Zeabur 项目设置中添加：

```
BOT_TOKEN=你的机器人Token
ADMIN_USER_IDS=你的用户ID
DATA_DIR=/data
```

**说明：**
- `DATA_DIR=/data` 将数据库存储在持久化 Volume 中
- 容器重启不会丢失数据

**获取方式：**
- BOT_TOKEN: 在 Telegram 搜索 @BotFather → `/token`
- ADMIN_USER_IDS: 在 Telegram 搜索 @userinfobot → 发送消息获取ID

### 4. 部署

点击 **"Deploy"** 按钮，等待部署完成

## 📝 文件说明

| 文件 | 说明 |
|------|------|
| `requirements.txt` | Python 依赖包列表 |
| `Procfile` | 启动命令配置 |
| `zeabur.json` | Zeabur 平台配置 |
| `.gitignore` | Git 忽略文件列表 |
| `runtime.txt` | Python 版本指定 |

## ⚠️ 重要提示

1. **不要提交敏感文件**
   - `config.py` 已在 `.gitignore` 中
   - 使用环境变量代替配置文件

2. **数据库持久化** ✅ 已解决
   - 代码已配置支持持久化存储
   - 设置 `DATA_DIR=/data` 环境变量
   - 在 Zeabur 添加 Volume（Mount Path: `/data`）
   - 数据库文件将存储在 Volume 中，容器重启不会丢失数据

3. **日志查看**
   - 在 Zeabur Dashboard 的 "Logs" 标签页查看运行日志

4. **自动重启**
   - 已配置自动重启策略
   - 机器人崩溃会自动重启（最多10次）

## 🔧 故障排查

### 问题：部署失败
- 检查 `requirements.txt` 是否正确
- 查看构建日志中的错误信息

### 问题：机器人无法启动
- 检查环境变量是否正确设置
- 查看运行日志中的错误信息
- 确认 BOT_TOKEN 格式正确

### 问题：权限错误
- 确认 ADMIN_USER_IDS 包含你的用户ID
- 用户ID 必须是数字，多个用逗号分隔（无空格）

## 📞 测试部署

部署成功后，在 Telegram 中：
1. 向机器人发送 `/start`（私聊）
2. 检查是否收到欢迎消息
3. 测试创建订单功能

## 🔄 更新部署

每次推送代码到 Git 仓库，Zeabur 会自动检测并重新部署。

```bash
git add .
git commit -m "Update code"
git push
```

## 🔄 从旧容器迁移数据（无Git仓库绑定）

如果旧版本部署是独立的容器（没有绑定Git仓库），迁移数据到新仓库部署的方法：

### 快速步骤

1. **备份旧数据**：在Zeabur Dashboard中找到旧容器的Volume，下载 `/data/loan_bot.db` 文件
2. **部署新版本**：创建新项目，配置Volume（`/data`）和环境变量
3. **上传数据库文件**：将下载的 `loan_bot.db` 上传到新项目的Volume `/data` 目录
4. **验证运行**：启动容器，检查日志并测试功能

### 详细步骤

请参考 **[DATA_MIGRATION.md](DATA_MIGRATION.md)** 文档，包含：
- 详细的下载和上传步骤
- 多种操作方法（Dashboard、终端、SSH）
- 验证和故障排查指南
- 注意事项和最佳实践

**优点**：
- 最简单直接，保留完整数据库状态
- 不需要额外的转换步骤
- 迁移后立即可用

**注意事项**：
- 确保两个部署使用相同的Volume挂载路径（`/data`）
- 确保新容器启动时能访问到Volume中的数据库文件
- 数据库Schema会自动迁移（使用 `CREATE TABLE IF NOT EXISTS` 和字段检查逻辑）

## 🧪 本地测试

### 1. 环境准备

```bash
# 检查Python版本（需要3.11）
python --version

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（或创建user_config.py）
# Windows PowerShell:
$env:BOT_TOKEN="你的机器人Token"
$env:ADMIN_USER_IDS="你的用户ID"

# Linux/Mac:
export BOT_TOKEN="你的机器人Token"
export ADMIN_USER_IDS="你的用户ID"
```

### 2. 数据库初始化

```bash
python init_db.py
```

这会创建 `loan_bot.db` 数据库文件（如果不存在）并初始化所有表结构。

### 3. 启动机器人

```bash
python main.py
```

机器人启动后，在Telegram中测试基本功能：
- 发送 `/start` 查看帮助信息
- 测试创建订单功能
- 测试查询报表功能

### 4. Docker本地测试（可选）

```bash
# 构建Docker镜像
docker build -t loan-bot .

# 运行容器（使用环境变量）
docker run --rm \
  -e BOT_TOKEN="你的机器人Token" \
  -e ADMIN_USER_IDS="你的用户ID" \
  -e DATA_DIR=/data \
  -v $(pwd)/data:/data \
  loan-bot

# 或者使用.env文件
docker run --rm --env-file .env -v $(pwd)/data:/data loan-bot
```

## 🔄 容器更新兼容性

### 数据库迁移机制

项目使用 `CREATE TABLE IF NOT EXISTS` 和字段检查逻辑，确保容器更新时：

- ✅ 现有表不会被覆盖
- ✅ 新字段会自动添加（如果缺失）
- ✅ 索引会自动创建（如果不存在）
- ✅ 现有数据不会丢失

### 更新流程

1. **备份数据**（推荐）
   - 使用 `/backup` 命令（如果已实现）
   - 或直接从Volume下载数据库文件

2. **部署新版本**
   - Zeabur会自动停止旧容器，启动新容器
   - 新容器启动时会运行 `init_db.init_database()`
   - 自动执行Schema迁移（只添加新字段，不删除现有字段）

3. **验证运行**
   - 检查日志确认数据库初始化成功
   - 测试基本功能（创建订单、查询报表等）

### 注意事项

- **Volume配置必须正确**：确保Volume挂载到 `/data`，环境变量 `DATA_DIR=/data`
- **向后兼容**：如果新版本有破坏性变更（删除字段、修改字段类型），需要额外的迁移脚本


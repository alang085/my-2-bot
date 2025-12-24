# Zeabur CLI 快速部署指南

## 📦 前置要求

- **Node.js** (LTS 版本)
  - 下载地址: https://nodejs.org/
  - 或使用包管理器安装

## 🚀 快速开始

### Windows 用户

1. **运行部署脚本**
   ```bash
   deploy_zeabur_cli.bat
   ```

2. **首次使用会要求登录**
   - 脚本会自动打开浏览器
   - 按照提示完成 Zeabur 账户登录

3. **等待部署完成**
   - 脚本会自动检查必要文件
   - 执行部署命令
   - 显示部署进度和结果

### Linux/Mac 用户

1. **设置执行权限（首次）**
   ```bash
   chmod +x deploy_zeabur_cli.sh
   ```

2. **运行部署脚本**
   ```bash
   ./deploy_zeabur_cli.sh
   ```

3. **首次使用会要求登录**
   - 脚本会自动打开浏览器
   - 按照提示完成 Zeabur 账户登录

4. **等待部署完成**

## 💻 手动命令部署

如果不想使用脚本，也可以直接使用命令：

```bash
# 1. 登录（首次使用）
npx zeabur@latest auth login

# 2. 部署
npx zeabur@latest deploy
```

## ⚙️ 部署后配置

部署完成后，需要在 Zeabur Dashboard 进行以下配置：

### 1. 配置环境变量

在项目设置 → Environment Variables 中添加：

```
BOT_TOKEN=你的机器人Token
ADMIN_USER_IDS=你的用户ID
DATA_DIR=/data
```

**获取方式：**
- **BOT_TOKEN**: 在 Telegram 搜索 `@BotFather` → 发送 `/token` → 选择你的机器人 → 复制 Token
- **ADMIN_USER_IDS**: 在 Telegram 搜索 `@userinfobot` → 发送消息 → 获取你的用户ID（数字）

### 2. 配置持久化存储

在项目设置 → Volumes 中添加：

- **Mount Path**: `/data`
- **Size**: 1GB（可根据需要调整）

**重要：** 数据库文件会存储在 Volume 中，容器重启不会丢失数据。

## 🔄 更新部署

直接再次运行部署脚本或命令即可：

```bash
# Windows
deploy_zeabur_cli.bat

# Linux/Mac
./deploy_zeabur_cli.sh

# 或直接使用命令
npx zeabur@latest deploy
```

## ✅ 验证部署

1. **查看日志**
   - 在 Zeabur Dashboard → Logs 标签页查看运行日志

2. **测试机器人**
   - 在 Telegram 中向机器人发送 `/start`
   - 检查是否收到欢迎消息

3. **测试功能**
   - 测试创建订单功能
   - 测试查询报表功能

## 🔧 故障排查

### 问题：Node.js 未安装

**解决方案：**
- 访问 https://nodejs.org/ 下载安装 LTS 版本
- 安装后重新运行脚本

### 问题：登录失败

**解决方案：**
- 检查网络连接
- 确保浏览器可以正常打开
- 手动运行 `npx zeabur@latest auth login`

### 问题：部署失败

**检查项：**
1. 网络连接是否正常
2. Zeabur 账户是否有权限
3. 必要文件是否存在：
   - `main.py`
   - `requirements.txt`
   - `Dockerfile`
   - `zeabur.json`
4. 查看错误信息，根据提示修复

### 问题：机器人无法启动

**检查项：**
1. 环境变量是否正确设置（BOT_TOKEN, ADMIN_USER_IDS）
2. Volume 是否正确挂载（Mount Path: `/data`）
3. 查看运行日志中的错误信息

## 📚 相关文档

- [完整部署指南](DEPLOY.md) - 包含 Git 部署方式
- [配置和数据库说明](CONFIG_AND_DATABASE.md)
- [生产环境部署指南](DEPLOYMENT.md)

## 🆚 CLI 部署 vs Git 部署

| 特性 | CLI 部署 | Git 部署 |
|------|---------|---------|
| 速度 | ⚡ 最快 | 中等 |
| 需要 Git 仓库 | ❌ 不需要 | ✅ 需要 |
| 自动部署 | ❌ 需手动运行 | ✅ 自动触发 |
| 适合场景 | 快速测试、一次性部署 | CI/CD、持续部署 |
| 版本管理 | 需手动管理 | 自动关联 Git 提交 |

**推荐：**
- 快速测试和部署 → 使用 **CLI 部署**
- 生产环境和持续集成 → 使用 **Git 部署**


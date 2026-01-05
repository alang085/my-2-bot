# Zeabur 部署指南

**版本**: 1.0  
**创建日期**: 2026-01-05  
**最后更新**: 2026-01-05

---

## 📋 概述

本文档提供在 Zeabur 平台上部署 `bot3` Telegram 机器人的详细步骤。

---

## 🚀 快速部署步骤

### 步骤 1: 准备 GitHub 仓库

1. **确保代码已推送到 GitHub**
   ```bash
   git add .
   git commit -m "准备 Zeabur 部署"
   git push origin main
   ```

2. **确认以下文件存在**:
   - ✅ `Dockerfile`
   - ✅ `requirements.txt`
   - ✅ `.gitignore`
   - ✅ `main.py`

---

### 步骤 2: 在 Zeabur 创建项目

1. **登录 Zeabur**
   - 访问 [Zeabur](https://zeabur.com)
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Import from GitHub"
   - 选择您的仓库

3. **选择服务类型**
   - Zeabur 会自动检测 Dockerfile
   - 选择 "Docker" 作为服务类型

---

### 步骤 3: 配置环境变量

在 Zeabur 项目设置中添加以下环境变量：

#### 必需环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `BOT_TOKEN` | Telegram Bot Token | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ADMIN_USER_IDS` | 管理员用户ID（逗号分隔，无空格） | `123456789,987654321` |

#### 可选环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATA_DIR` | 数据目录路径 | `/app/data` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `DEBUG` | 调试模式 | `0` |

#### 在 Zeabur 中设置环境变量

1. 进入项目设置
2. 点击 "Environment Variables"
3. 添加每个环境变量：
   - 点击 "Add Variable"
   - 输入变量名和值
   - 点击 "Save"

---

### 步骤 4: 配置持久化存储

1. **创建存储卷**
   - 在项目设置中，找到 "Storage" 或 "Volumes"
   - 创建新的存储卷，命名为 `data`
   - 挂载路径设置为 `/app/data`

2. **挂载到服务**
   - 在服务设置中，找到 "Volumes"
   - 将 `data` 卷挂载到 `/app/data`

**重要**: 这确保数据库文件在重启后仍然存在。

---

### 步骤 5: 部署

1. **触发部署**
   - Zeabur 会自动检测代码推送并触发部署
   - 或手动点击 "Redeploy"

2. **查看部署日志**
   - 在项目页面查看构建日志
   - 确认构建成功

3. **检查运行状态**
   - 查看服务状态，应显示 "Running"
   - 查看日志，确认机器人已启动

---

## 🔍 验证部署

### 检查日志

在 Zeabur 项目页面：

1. 点击服务名称
2. 查看 "Logs" 标签
3. 确认看到以下日志：
   ```
   机器人启动中... 管理员数量: X
   数据库已就绪
   应用创建成功
   机器人启动成功，等待消息...
   ```

### 测试机器人

1. 在 Telegram 中搜索您的机器人
2. 发送 `/start` 命令
3. 确认收到欢迎消息

---

## 🛠️ 配置说明

### 自动检测配置

Zeabur 会自动检测以下配置：

- **Dockerfile**: 如果存在，会使用 Docker 构建
- **Python 项目**: 如果检测到 `requirements.txt`，会安装依赖
- **启动命令**: 默认运行 `main.py`

### 自定义配置

如果需要自定义配置，可以创建 `zeabur.json`：

```json
{
  "version": 2,
  "buildCommand": "pip install -r requirements.txt",
  "devCommand": "python main.py",
  "installCommand": "pip install -r requirements.txt",
  "dockerfile": "Dockerfile"
}
```

---

## 📊 监控和维护

### 查看日志

1. **实时日志**
   - 在 Zeabur 项目页面查看实时日志
   - 使用日志搜索功能查找特定错误

2. **日志级别**
   - 设置 `LOG_LEVEL=DEBUG` 查看详细日志
   - 生产环境建议使用 `LOG_LEVEL=INFO`

### 重启服务

1. **手动重启**
   - 在服务页面点击 "Restart"
   - 或使用 Zeabur CLI

2. **自动重启**
   - Zeabur 会自动重启崩溃的服务
   - 检查日志了解重启原因

### 更新部署

1. **自动更新**
   - 推送代码到 GitHub 会自动触发部署
   - 或配置 Webhook 触发部署

2. **手动更新**
   - 在项目页面点击 "Redeploy"
   - 选择要部署的分支或提交

---

## 🔧 故障排除

### 问题 1: 构建失败

**错误**: `Build failed` 或 `Docker build error`

**解决方案**:
1. 检查 Dockerfile 语法
2. 确认 `requirements.txt` 存在且格式正确
3. 查看构建日志中的具体错误信息
4. 确保所有依赖都在 `requirements.txt` 中

### 问题 2: 服务无法启动

**错误**: `Service failed to start` 或 `Exit code 1`

**解决方案**:
1. 检查环境变量是否正确设置
2. 查看日志中的错误信息
3. 确认 `BOT_TOKEN` 和 `ADMIN_USER_IDS` 已设置
4. 检查数据库初始化是否成功

### 问题 3: 机器人无响应

**错误**: 机器人不响应命令

**解决方案**:
1. 检查日志，确认机器人已启动
2. 验证 `BOT_TOKEN` 是否正确
3. 确认网络连接正常
4. 检查是否有 Conflict 错误（多个实例）

### 问题 4: 数据丢失

**错误**: 重启后数据丢失

**解决方案**:
1. 确认已创建并挂载存储卷
2. 检查存储卷挂载路径是否正确（`/app/data`）
3. 验证存储卷有足够的空间
4. 检查文件权限

---

## 🔐 安全建议

1. **保护敏感信息**
   - 使用 Zeabur 环境变量存储 `BOT_TOKEN`
   - 不要将敏感信息提交到 Git
   - 定期轮换 Bot Token

2. **访问控制**
   - 限制 Zeabur 项目访问权限
   - 使用团队协作功能管理访问

3. **监控**
   - 启用日志监控
   - 设置异常告警
   - 定期检查服务状态

---

## 📈 性能优化

1. **资源分配**
   - 根据使用情况调整 CPU 和内存
   - 监控资源使用情况

2. **数据库优化**
   - 定期备份数据库
   - 监控数据库文件大小
   - 考虑使用外部数据库（如 PostgreSQL）

3. **日志管理**
   - 定期清理旧日志
   - 使用日志聚合服务（可选）

---

## 🔄 持续部署

### 自动部署

Zeabur 支持以下自动部署方式：

1. **GitHub 推送触发**
   - 推送到 `main` 分支自动部署
   - 可在设置中配置分支

2. **Webhook 触发**
   - 配置 Webhook URL
   - 通过 API 触发部署

### 部署策略

1. **蓝绿部署**（推荐）
   - 创建新版本
   - 测试通过后切换流量

2. **滚动更新**
   - 逐步更新实例
   - 最小化停机时间

---

## 📚 相关资源

- [Zeabur 文档](https://zeabur.com/docs)
- [Zeabur CLI](https://zeabur.com/docs/cli)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [启动指南](./STARTUP_GUIDE.md)

---

## 🎯 部署检查清单

- [ ] 代码已推送到 GitHub
- [ ] Dockerfile 已创建
- [ ] requirements.txt 已创建
- [ ] 环境变量已配置（BOT_TOKEN, ADMIN_USER_IDS）
- [ ] 存储卷已创建并挂载
- [ ] 服务已成功部署
- [ ] 日志显示机器人已启动
- [ ] 机器人响应测试命令
- [ ] 数据持久化正常

---

## 💡 提示

1. **首次部署**
   - 建议先在测试环境部署
   - 验证所有功能正常后再部署到生产环境

2. **备份**
   - 定期备份数据库文件
   - 使用 Zeabur 的备份功能或手动导出

3. **监控**
   - 设置监控告警
   - 定期检查服务健康状态

---

**维护者**: 开发团队  
**最后更新**: 2026-01-05


# Zeabur 快速部署指南

## 🚀 5 分钟快速部署

### 步骤 1: 推送代码到 GitHub

```bash
git add .
git commit -m "准备 Zeabur 部署"
git push origin main
```

### 步骤 2: 在 Zeabur 创建项目

1. 访问 [Zeabur](https://zeabur.com)
2. 使用 GitHub 登录
3. 点击 "New Project" → "Import from GitHub"
4. 选择您的仓库

### 步骤 3: 配置环境变量

在项目设置 → Environment Variables 中添加：

| 变量名 | 值 |
|--------|-----|
| `BOT_TOKEN` | 您的 Telegram Bot Token |
| `ADMIN_USER_IDS` | 管理员用户ID（逗号分隔，无空格） |

**示例**:
- `BOT_TOKEN`: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
- `ADMIN_USER_IDS`: `123456789,987654321`

### 步骤 4: 配置存储卷（重要！）

1. 在项目设置中找到 "Storage" 或 "Volumes"
2. 创建新存储卷，命名为 `data`
3. 在服务设置中，将 `data` 卷挂载到 `/app/data`

**为什么需要？** 这确保数据库文件在重启后不会丢失。

### 步骤 5: 部署

Zeabur 会自动检测 Dockerfile 并开始构建。等待部署完成。

### 步骤 6: 验证

1. 查看日志，确认看到：
   ```
   机器人启动中... 管理员数量: X
   数据库已就绪
   机器人启动成功，等待消息...
   ```

2. 在 Telegram 中测试：
   - 发送 `/start` 给机器人
   - 确认收到欢迎消息

---

## ✅ 部署检查清单

- [ ] 代码已推送到 GitHub
- [ ] 在 Zeabur 创建了项目
- [ ] 配置了 `BOT_TOKEN` 环境变量
- [ ] 配置了 `ADMIN_USER_IDS` 环境变量
- [ ] 创建并挂载了 `data` 存储卷
- [ ] 部署成功
- [ ] 日志显示机器人已启动
- [ ] 机器人响应测试命令

---

## 🔧 常见问题

### Q: 构建失败怎么办？

**A**: 检查：
1. Dockerfile 是否存在
2. requirements.txt 是否存在
3. 查看构建日志中的具体错误

### Q: 机器人无响应？

**A**: 检查：
1. `BOT_TOKEN` 是否正确
2. 日志中是否有错误
3. 是否有 Conflict 错误（多个实例）

### Q: 数据丢失？

**A**: 确保：
1. 已创建存储卷
2. 存储卷已挂载到 `/app/data`
3. 检查存储卷状态

---

## 📚 详细文档

查看完整部署指南：`docs/ZEABUR_DEPLOYMENT.md`

---

**提示**: 首次部署建议先在测试环境验证，确认无误后再部署到生产环境。


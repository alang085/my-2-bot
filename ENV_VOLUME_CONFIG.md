# 环境变量和持久化存储配置指南

## 📋 配置清单

### 必须配置的环境变量

```
BOT_TOKEN=你的机器人Token
ADMIN_USER_IDS=你的用户ID（多个用逗号分隔，无空格）
DATA_DIR=/data
```

### 必须配置的持久化存储

- **Mount Path**: `/data`
- **用途**: 存储 SQLite 数据库文件（`loan_bot.db`）
- **大小**: 建议至少 1GB（根据数据量调整）

---

## 🔧 在不同平台配置

### 方案1：Zeabur 配置

#### 步骤1：配置环境变量

1. 在 Zeabur Dashboard 中找到你的项目
2. 进入项目设置
3. 找到 **"Environment Variables"** 或 **"Variables"** 标签页
4. 点击 **"Add Variable"** 或 **"New Variable"**
5. 添加以下变量：

   **变量1**：
   - **Name**: `BOT_TOKEN`
   - **Value**: `你的机器人Token`
   - **类型**: Secret（推荐，会隐藏显示）

   **变量2**：
   - **Name**: `ADMIN_USER_IDS`
   - **Value**: `你的用户ID`（例如：`123456789`，多个用逗号分隔：`123456789,987654321`）
   - **类型**: Secret（推荐）

   **变量3**：
   - **Name**: `DATA_DIR`
   - **Value**: `/data`
   - **类型**: Plain（普通变量）

6. 保存配置

#### 步骤2：配置持久化存储（Volume）

1. 在项目设置中找到 **"Storage"** 或 **"Volumes"** 标签页
2. 点击 **"Add Volume"** 或 **"Create Volume"**
3. 配置 Volume：
   - **Mount Path**: `/data`
   - **Size**: `1GB`（或根据需要调整，建议至少 500MB）
4. 保存配置

#### 步骤3：部署或重启服务

- 如果服务已部署，需要重启以应用新的环境变量和Volume配置
- 新部署会自动应用配置

---

### 方案2：Railway 配置

#### 步骤1：配置环境变量

1. 在 Railway Dashboard 中找到你的服务
2. 点击服务进入详情页
3. 点击 **"Variables"** 标签页
4. 点击 **"New Variable"**
5. 添加以下变量：

   **变量1**：
   - **Key**: `BOT_TOKEN`
   - **Value**: `你的机器人Token`
   - **类型**: Secret

   **变量2**：
   - **Key**: `ADMIN_USER_IDS`
   - **Value**: `你的用户ID`
   - **类型**: Secret

   **变量3**：
   - **Key**: `DATA_DIR`
   - **Value**: `/data`
   - **类型**: Plain

6. 保存（Railway 会自动应用）

#### 步骤2：配置持久化存储

1. 在服务详情页，点击 **"Settings"** 标签页
2. 找到 **"Volumes"** 部分
3. 点击 **"Add Volume"** 或 **"Create Volume"**
4. 配置：
   - **Mount Path**: `/data`
   - **Size**: `1GB`
5. 保存

#### 步骤3：重启服务

- Railway 会自动检测配置变化并重启服务
- 或手动点击 **"Redeploy"**

---

## 📝 获取配置值

### 获取 BOT_TOKEN

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/mybots`
3. 选择你的机器人
4. 点击 `API Token`
5. 复制 Token

**格式示例**：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 获取 ADMIN_USER_IDS

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息
3. 获取你的用户ID（纯数字）

**格式**：
- 单个用户：`123456789`
- 多个用户：`123456789,987654321`（用逗号分隔，**无空格**）

---

## ✅ 验证配置

### 方法1：查看容器日志

部署后查看日志，应该看到：

```
数据库 /data/loan_bot.db 初始化完成！
机器人启动中...
管理员数量: X
机器人已启动，等待消息...
```

如果没有 `DATA_DIR` 环境变量，可能显示：
```
数据库 /app/loan_bot.db 初始化完成！
```

### 方法2：在 Telegram 中测试

1. 向机器人发送 `/start`（私聊）
2. 应该收到欢迎消息
3. 如果能正常响应，说明配置正确

### 方法3：检查数据库文件位置

如果平台支持容器终端访问：

```bash
# 进入容器终端
ls -lh /data/
# 应该看到 loan_bot.db 文件

# 检查环境变量
echo $DATA_DIR
# 应该输出：/data

# 检查其他环境变量（注意：Secret类型可能不显示）
echo $BOT_TOKEN  # 可能显示为空或隐藏
```

---

## ⚠️ 常见问题和解决方案

### 问题1：数据库文件不在 /data 目录

**原因**：`DATA_DIR` 环境变量未设置或错误

**解决**：
- 检查环境变量 `DATA_DIR` 是否设置为 `/data`
- 确保 Volume 已正确挂载到 `/data`

### 问题2：数据丢失（容器重启后）

**原因**：未配置 Volume 持久化存储

**解决**：
- 配置 Volume，Mount Path 设置为 `/data`
- 确保环境变量 `DATA_DIR=/data`

### 问题3：权限错误

**原因**：Volume 挂载权限问题

**解决**：
- 确保 Volume 有读写权限
- 检查容器日志中的权限错误信息

### 问题4：环境变量未生效

**原因**：服务未重启

**解决**：
- 重启服务以应用新的环境变量
- 或重新部署服务

---

## 📊 配置检查清单

部署前确认：

- [ ] `BOT_TOKEN` 环境变量已设置
- [ ] `ADMIN_USER_IDS` 环境变量已设置（格式正确，逗号分隔无空格）
- [ ] `DATA_DIR` 环境变量已设置为 `/data`
- [ ] Volume 已创建并挂载到 `/data`
- [ ] Volume 大小足够（至少 500MB，建议 1GB）
- [ ] 服务已重启以应用配置
- [ ] 日志显示数据库在 `/data` 目录初始化
- [ ] Telegram 机器人能正常响应

---

## 🔐 安全建议

1. **使用 Secret 类型存储敏感信息**：
   - `BOT_TOKEN` 设置为 Secret
   - `ADMIN_USER_IDS` 可以设置为 Secret

2. **不要提交敏感信息到 Git**：
   - ✅ 使用环境变量
   - ❌ 不要在代码中硬编码
   - ✅ `user_config.py` 已在 `.gitignore` 中

3. **定期备份数据库**：
   - 从 Volume 下载 `loan_bot.db` 文件
   - 或使用备份命令（如果已实现）

---

## 📚 相关文档

- [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) - 完整部署计划
- [DATA_MIGRATION.md](DATA_MIGRATION.md) - 数据迁移指南
- [CONFIG_AND_DATABASE.md](CONFIG_AND_DATABASE.md) - 配置和数据库说明


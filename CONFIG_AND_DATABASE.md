# 配置和数据库说明

## 🔐 BOT_TOKEN 配置方式

### config.py 的配置逻辑

`config.py` 使用 `load_config()` 函数，按以下优先级加载配置：

1. **优先级1：环境变量**（推荐用于生产环境）
   ```bash
   # Windows PowerShell
   $env:BOT_TOKEN="你的机器人Token"
   $env:ADMIN_USER_IDS="你的用户ID"
   
   # Linux/Mac
   export BOT_TOKEN="你的机器人Token"
   export ADMIN_USER_IDS="你的用户ID"
   ```

2. **优先级2：user_config.py 文件**（用于本地开发）
   ```python
   # user_config.py
   BOT_TOKEN = '你的机器人Token'
   ADMIN_USER_IDS = '你的用户ID1,你的用户ID2'
   ```

### 在容器/生产环境中的配置

**推荐使用环境变量**，因为：
- ✅ 更安全（不会提交到Git）
- ✅ 便于在不同环境切换
- ✅ 符合12-factor应用原则

在 Zeabur/Railway 等平台部署时：
```
环境变量：
BOT_TOKEN=你的机器人Token
ADMIN_USER_IDS=你的用户ID
DATA_DIR=/data
```

### 获取 BOT_TOKEN

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/mybots` 查看你的机器人
3. 选择你的机器人 → `API Token`
4. 复制 Token

### 获取 ADMIN_USER_IDS

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息
3. 获取你的用户ID（数字）

---

## 🗄️ 数据库说明

### 是的，这个机器人需要数据库

机器人使用 **SQLite** 数据库存储所有业务数据。

### 数据库文件

- **文件名**：`loan_bot.db`
- **存储位置**：由环境变量 `DATA_DIR` 指定
  - 默认：项目根目录
  - 生产环境：`/data`（Volume挂载路径）

### 数据库用途

数据库存储以下数据：

1. **订单数据**（orders表）
   - 订单信息、状态、金额等

2. **财务数据**（financial_data表）
   - 全局财务统计

3. **分组数据**（grouped_data表）
   - 按归属ID分组的统计

4. **收入明细**（income_records表）
   - 每笔收入记录

5. **支出明细**（expense_records表）
   - 每笔支出记录

6. **用户权限**（authorized_users表）
   - 授权用户列表

7. **支付账号**（payment_accounts表）
   - GCASH、PayMaya账号信息

8. **定时任务**（scheduled_broadcasts表）
   - 定时播报配置

9. **操作历史**（operation_history表）
   - 用于撤销功能

10. **其他表**：daily_data、group_message_config、company_announcements 等

### 数据库初始化

容器启动时会自动初始化：

1. 检查数据库文件是否存在
2. 如果不存在，运行 `init_db.init_database()`
3. 创建所有必要的表
4. 自动执行 Schema 迁移（添加新字段等）

### 数据持久化（重要！）

**在生产环境中必须配置 Volume**：

- **Mount Path**: `/data`
- **环境变量**: `DATA_DIR=/data`
- **数据库文件**: `/data/loan_bot.db`

这样确保：
- ✅ 容器重启不会丢失数据
- ✅ 数据存储在持久化存储中
- ✅ 可以备份和迁移数据

---

## 📋 部署时需要的配置

### 环境变量（必须）

```
BOT_TOKEN=你的机器人Token
ADMIN_USER_IDS=你的用户ID（多个用逗号分隔）
DATA_DIR=/data
```

### Volume 配置（必须）

- **Mount Path**: `/data`
- **Size**: 至少 500MB（建议1GB）

### 数据库文件（可选，用于迁移）

如果从旧部署迁移数据：
- 上传 `loan_bot.db` 到 Volume 的 `/data` 目录
- 或上传 `database_backup.sql` 到 `/data` 目录（会自动导入）

---

## 🎯 总结

1. **BOT_TOKEN 配置**：
   - 优先使用环境变量（生产环境）
   - 或使用 user_config.py（本地开发）
   - 容器部署时通过环境变量配置

2. **数据库**：
   - ✅ **必须**使用数据库
   - ✅ 使用 SQLite（`loan_bot.db`）
   - ✅ 必须配置 Volume 持久化存储
   - ✅ 容器启动时自动初始化

3. **部署要求**：
   - 环境变量：BOT_TOKEN、ADMIN_USER_IDS、DATA_DIR
   - Volume：挂载到 `/data`
   - 数据库会自动创建和管理


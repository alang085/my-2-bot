# 机器人启动指南

## ⚠️ 重要提示

**Telegram Bot API 限制：同一时间只能有一个机器人实例运行！**

如果看到错误：`Conflict: terminated by other getUpdates request`，说明已经有另一个实例在运行。

## 🔧 解决冲突问题

### 方法1：停止所有实例（推荐）
```bash
# 停止所有运行的机器人实例
pkill -9 -f "python3 main.py"

# 等待几秒
sleep 3

# 确认没有运行的实例
ps aux | grep "python3 main.py" | grep -v grep

# 重新启动
python3 main.py
```

### 方法2：查找并手动停止
```bash
# 查找运行的进程
ps aux | grep "python3 main.py"

# 手动停止（替换 PID 为实际进程ID）
kill -9 <PID>
```

### 方法3：检查其他终端/服务器
- 检查是否有其他终端窗口运行了机器人
- 检查是否有其他服务器/服务运行了机器人
- 检查是否有后台任务（cron, systemd等）运行了机器人

## 🚀 正确启动方式

### 前台运行（用于测试）
```bash
cd /Users/macbookair/Downloads/未命名文件夹/loan005.bot/bot3
python3 main.py
```

### 后台运行（用于生产）
```bash
# 使用 nohup
cd /Users/macbookair/Downloads/未命名文件夹/loan005.bot/bot3
nohup python3 main.py > bot.log 2>&1 &

# 或使用 screen
screen -S bot3
python3 main.py
# 按 Ctrl+A 然后 D 来分离会话
```

## 📊 启动成功标志

看到以下日志表示启动成功：
```
机器人启动中... 管理员数量: 1
检查数据库...
数据库初始化完成
数据库已就绪
应用创建成功
机器人启动成功，等待消息...
Scheduler started
```

## 🔍 监控运行状态

### 查看实时日志
```bash
tail -f bot_runtime.log
# 或
tail -f bot.log
```

### 检查进程
```bash
ps aux | grep "python3 main.py" | grep -v grep
```

### 查看最新日志
```bash
tail -30 bot_runtime.log
```

## ⚠️ 常见问题

### 1. Conflict 错误
**原因**: 多个实例同时运行  
**解决**: 停止所有实例，只保留一个

### 2. 数据库错误
**原因**: 数据库文件权限问题或损坏  
**解决**: 检查数据库文件权限，必要时重新初始化

### 3. 网络错误
**原因**: 无法连接到 Telegram API  
**解决**: 检查网络连接，确认可以访问 api.telegram.org

### 4. Token 错误
**原因**: BOT_TOKEN 不正确或已失效  
**解决**: 检查 user_config.py 或环境变量中的 BOT_TOKEN

## 📝 当前状态

根据日志显示：
- ✅ 机器人已成功启动
- ✅ 数据库已初始化
- ✅ Application 创建成功
- ✅ 调度器已启动
- ⚠️ 检测到冲突（可能有其他实例在运行）

## 🎯 下一步

1. **停止所有实例**: 使用 `pkill -9 -f "python3 main.py"`
2. **等待几秒**: 确保所有进程完全停止
3. **重新启动**: 运行 `python3 main.py`
4. **测试功能**: 在 Telegram 中发送 `/start` 测试


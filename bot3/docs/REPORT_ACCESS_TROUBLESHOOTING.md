# 报表访问问题排查指南

## 问题描述
私聊中无法访问报表功能（`/report` 或 `/myreport` 命令无响应）

## 可能的原因

### 1. `/report` 命令无法使用

**原因**: 需要用户已授权（管理员或员工）

**检查方法**:
- 用户必须是管理员（在 `ADMIN_IDS` 中）
- 或者用户已被添加为授权员工

**解决方案**:
```bash
# 管理员可以使用以下命令添加员工：
/add_employee <用户ID>
```

**权限要求**:
- `@authorized_required` - 需要用户已授权
- `@private_chat_only` - 只能在私聊中使用

### 2. `/myreport` 命令无法使用

**原因**: 用户没有分配归属ID

**检查方法**:
- 用户必须有归属ID映射才能使用此命令
- 如果没有归属ID，会显示错误消息："❌ 您没有权限查看任何归属ID的报表"

**解决方案**:
```bash
# 管理员可以使用以下命令为用户分配归属ID：
/set_user_group_id <用户ID> <归属ID>
```

**权限要求**:
- `@private_chat_only` - 只能在私聊中使用
- 不需要 `@authorized_required`，但需要归属ID

### 3. 机器人未正常运行

**原因**: 机器人进程未运行或出现冲突

**检查方法**:
```bash
# 检查进程
ps aux | grep "python3 main.py" | grep -v grep

# 查看日志
tail -f bot_runtime.log
```

**解决方案**:
```bash
# 停止所有实例
pkill -9 -f "python3 main.py"

# 等待几秒
sleep 5

# 重新启动
python3 main.py
```

## 诊断步骤

### 步骤1: 检查用户权限
```bash
# 在 Telegram 中发送
/check_permission
```

这会显示：
- 用户ID
- 是否为管理员
- 是否为授权用户
- 可访问的归属ID列表

### 步骤2: 检查数据库
```python
# 检查授权用户
SELECT * FROM authorized_users;

# 检查用户归属映射
SELECT * FROM user_group_mapping;
```

### 步骤3: 查看日志
```bash
tail -f bot_runtime.log | grep -i "report\|error\|permission"
```

## 常见错误消息

### "⚠️ Permission denied."
**原因**: 用户未授权（不是管理员也不是员工）  
**解决**: 使用 `/add_employee <用户ID>` 添加用户

### "❌ 您没有权限查看任何归属ID的报表"
**原因**: 用户没有分配归属ID  
**解决**: 使用 `/set_user_group_id <用户ID> <归属ID>` 分配归属ID

### "❌ 无法获取用户信息"
**原因**: Telegram 更新对象中没有用户信息  
**解决**: 检查机器人是否正常运行，重新发送命令

## 快速修复

### 如果是管理员
管理员可以直接使用 `/report` 命令，无需额外配置。

### 如果是普通用户
1. **使用 `/report`**: 需要先被添加为员工
   ```
   管理员执行: /add_employee <你的用户ID>
   ```

2. **使用 `/myreport`**: 需要分配归属ID
   ```
   管理员执行: /set_user_group_id <你的用户ID> <归属ID>
   ```

## 验证修复

修复后，测试以下命令：
1. `/check_permission` - 检查权限状态
2. `/report` - 测试报表命令（需要授权）
3. `/myreport` - 测试我的报表命令（需要归属ID）

## 相关命令

### 管理员命令
- `/add_employee <用户ID>` - 添加授权员工
- `/remove_employee <用户ID>` - 移除授权员工
- `/list_employees` - 列出所有授权员工
- `/set_user_group_id <用户ID> <归属ID>` - 设置用户归属ID
- `/remove_user_group_id <用户ID>` - 移除用户归属ID
- `/list_user_group_mappings` - 列出所有用户归属映射

### 用户命令
- `/check_permission` - 检查自己的权限状态
- `/report` - 查看报表（需要授权）
- `/myreport` - 查看我的报表（需要归属ID）


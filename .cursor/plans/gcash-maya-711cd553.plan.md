<!-- 711cd553-e1b4-4a1f-a7f7-aa1f259c7d77 c4e531d0-1716-4813-be6c-07d1069698a7 -->
# 整理机器人命令菜单

## 需要从命令菜单中移除的命令（保留功能）

1. `/schedule` - 定时播报管理（保留功能，仅从菜单移除）
2. `/gcash` - 查看GCash账户（保留功能，仅从菜单移除）
3. `/paymaya` - 查看PayMaya账户（保留功能，仅从菜单移除）
4. `/accounts` - 查看所有账户（保留功能，仅从菜单移除）

## 账户总余额查看

账户总余额通过 `/balance_history` 命令查看：

- 权限：私聊，需要授权（authorized_required）
- 功能：显示GCash和PayMaya的总余额
- 支持查看历史记录

## 整理任务

### 1. 从 Telegram 命令菜单中移除（main.py）

在 `main.py` 的 `post_init` 函数中，从 `commands` 列表中移除：

- `("schedule", "Manage scheduled broadcasts")`
- `("accounts", "View all payment accounts")`
- `("gcash", "GCASH account info")`
- `("paymaya", "PayMaya account info")`

**注意：** 不删除 `CommandHandler` 注册，命令功能仍然可用。

### 2. 保留所有功能

**不修改以下内容：**

- ✅ 保留所有 `CommandHandler` 注册（命令功能仍然可用）
- ✅ 保留 `start` 命令中的帮助信息（用户仍可在帮助中看到这些命令）
- ✅ 用户仍可通过直接输入命令使用这些功能

**仅修改：**

- ❌ 从 Telegram Bot Commands Menu 中移除（用户输入 `/` 时不会显示这4个命令）

### To-dos

- [ ] 检查数据库操作函数的事务提交和一致性
- [ ] 检查订单创建和更新逻辑的数据一致性
- [ ] 检查财务统计更新的一致性
- [ ] 检查收入记录和统计的一致性
- [ ] 使用工具强化代码（类型检查、linting等）
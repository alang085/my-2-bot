# Excel报表权限扩展到员工 - 实施计划

## 目标
将Excel报表的查看权限从仅管理员扩展到员工（authorized_required），但保持合并功能仅限管理员。

## 需要修改的功能

### 1. 增量报表预览 ✅ 扩展到员工
- **文件**: `handlers/command_handlers.py`
- **函数**: `preview_incremental_report_cmd`
- **当前权限**: `@admin_required`
- **修改为**: `@authorized_required`
- **说明**: 预览功能只是查看，不修改数据，可以给员工权限

### 2. 增量报表合并 ⚠️ 保持管理员权限
- **文件**: `handlers/command_handlers.py`
- **函数**: `merge_incremental_report_cmd`
- **当前权限**: `@admin_required`
- **保持不变**: `@admin_required`
- **说明**: 合并功能会影响全局数据，必须保持管理员权限

### 3. 每日数据变更表 ✅ 扩展到员工
- **文件**: `handlers/daily_changes_handlers.py`
- **函数**: `show_daily_changes_table`
- **当前权限**: `@admin_required`
- **修改为**: `@authorized_required`
- **说明**: 查看每日数据变更，不修改数据，可以给员工权限

### 4. 订单总表Excel ✅ 扩展到员工
- **文件**: `handlers/order_table_handlers.py`
- **函数**: `show_order_table`
- **当前权限**: 手动检查管理员（`_is_admin`）
- **修改为**: 使用 `@authorized_required` 装饰器
- **说明**: 导出订单总表Excel，不修改数据，可以给员工权限

### 5. 合并回调 ⚠️ 保持管理员权限
- **文件**: `callbacks/incremental_merge_callbacks.py`
- **函数**: `handle_incremental_merge_callback`
- **当前权限**: 手动检查管理员（`ADMIN_IDS`）
- **保持不变**: 保持管理员权限检查
- **说明**: 合并功能会影响全局数据，必须保持管理员权限

## 修改清单

### 文件1: handlers/command_handlers.py

**修改1**: `preview_incremental_report_cmd`
```python
# 修改前
@admin_required
@private_chat_only
@error_handler
async def preview_incremental_report_cmd(...)

# 修改后
@authorized_required
@private_chat_only
@error_handler
async def preview_incremental_report_cmd(...)
```

**修改2**: `merge_incremental_report_cmd`
- 保持不变（保持 `@admin_required`）

### 文件2: handlers/daily_changes_handlers.py

**修改**: `show_daily_changes_table`
```python
# 修改前
@admin_required
@private_chat_only
@error_handler
async def show_daily_changes_table(...)

# 修改后
@authorized_required
@private_chat_only
@error_handler
async def show_daily_changes_table(...)
```

### 文件3: handlers/order_table_handlers.py

**修改**: `show_order_table`
```python
# 修改前
async def show_order_table(...):
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_admin(user_id):
        await update.message.reply_text("❌ 此功能仅限管理员使用")
        return

# 修改后
@authorized_required
@private_chat_only
@error_handler
async def show_order_table(...):
    # 移除手动权限检查，使用装饰器
```

### 文件4: callbacks/incremental_merge_callbacks.py

**保持不变**: `handle_incremental_merge_callback`
- 保持管理员权限检查（合并功能必须限制）

## 权限说明

### 员工权限（authorized_required）
- ✅ 预览增量报表
- ✅ 查看每日数据变更表
- ✅ 导出订单总表Excel
- ❌ 合并增量报表（仅管理员）

### 管理员权限（admin_required）
- ✅ 所有员工权限
- ✅ 合并增量报表
- ✅ 合并回调操作

## 实施步骤

1. 修改 `handlers/command_handlers.py` - 预览功能权限
2. 修改 `handlers/daily_changes_handlers.py` - 每日变更表权限
3. 修改 `handlers/order_table_handlers.py` - 订单总表权限
4. 验证合并功能仍限制为管理员
5. 测试员工权限是否正常工作


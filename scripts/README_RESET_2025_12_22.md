# 数据重置脚本使用说明

## 📋 脚本功能

此脚本用于将 **2025-12-22** 的统计数据（除了延续性数据）全部归零，使系统回到日切后的状态。

## 🔒 延续性数据（保留）

以下数据**不会被重置**，会保留原值：

- `valid_orders` - 有效订单数
- `valid_amount` - 有效金额
- `liquid_funds` - 流动资金

## 🔄 需要归零的数据

以下数据**会被重置为0或删除**：

### 1. financial_data 表
- `new_clients` - 新客户数
- `new_clients_amount` - 新客户金额
- `old_clients` - 老客户数
- `old_clients_amount` - 老客户金额
- `interest` - 利息
- `completed_orders` - 完成订单数
- `completed_amount` - 完成金额
- `breach_orders` - 违约订单数
- `breach_amount` - 违约金额
- `breach_end_orders` - 违约完成订单数
- `breach_end_amount` - 违约完成金额

### 2. grouped_data 表
- 所有分组的所有非延续性字段（同上）

### 3. daily_data 表
- **2025-12-22** 的所有记录（全部删除）

### 4. income_records 表
- **2025-12-22** 的所有收入记录（标记为已撤销，`is_undone = 1`）

### 5. expense_records 表
- **2025-12-22** 的所有支出记录（删除）

## ⚠️ 注意事项

1. **此脚本是一次性的**，执行后无法恢复（除了延续性数据）
2. **执行前请确认**：确保你真的需要重置 2025-12-22 的数据
3. **备份建议**：执行前建议备份数据库文件 `loan_bot.db`
4. **操作历史**：`operation_history` 表中的记录不会被删除，保留完整历史
5. **订单数据**：`orders` 表中的订单数据不会被删除，只重置统计数据

## 🚀 执行方式

### Windows

**方式1：双击执行**
```
双击 scripts/reset_daily_data_2025_12_22.bat
```

**方式2：命令行执行**
```cmd
cd 项目根目录
python scripts\reset_daily_data_2025_12_22.py
```

### Linux/Mac

**方式1：使用Shell脚本**
```bash
bash scripts/reset_daily_data_2025_12_22.sh
```

**方式2：直接执行Python**
```bash
cd 项目根目录
python3 scripts/reset_daily_data_2025_12_22.py
```

## 📊 执行流程

1. **显示警告信息**：提示用户将要执行的操作
2. **用户确认**：需要输入 `yes` 确认执行
3. **开始事务**：所有操作在事务中执行
4. **执行重置**：
   - 重置 financial_data 表
   - 重置 grouped_data 表
   - 删除 daily_data 表中的 2025-12-22 记录
   - 标记 income_records 表中的 2025-12-22 记录为已撤销
   - 删除 expense_records 表中的 2025-12-22 记录
5. **提交事务**：所有操作成功后才提交
6. **生成报告**：显示重置后的数据状态

## 📝 执行示例

```
============================================================
开始执行数据重置脚本
目标日期: 2025-12-22
============================================================

⚠️  警告：此脚本将重置 2025-12-22 的所有统计数据（除了延续性数据）
延续性数据（保留）：valid_orders, valid_amount, liquid_funds

需要归零的数据：
  - financial_data 表中的非延续性字段
  - grouped_data 表中的非延续性字段
  - daily_data 表中 2025-12-22 的所有数据
  - income_records 表中 2025-12-22 的记录（标记为已撤销）
  - expense_records 表中 2025-12-22 的记录（删除）

确认执行？(yes/no): yes

2025-01-16 10:00:00 - INFO - 开始重置 financial_data 表...
2025-01-16 10:00:00 - INFO - 保留延续性数据: valid_orders=100, valid_amount=50000.00, liquid_funds=100000.00
2025-01-16 10:00:00 - INFO - ✅ financial_data 表重置完成
...

✅ 所有操作已成功完成并提交
```

## 🔍 验证结果

执行完成后，脚本会生成一份报告，显示：
- financial_data 表的当前值
- grouped_data 表的统计信息
- daily_data 表中 2025-12-22 的记录数（应该为0）
- income_records 表中 2025-12-22 的记录数和已撤销记录数
- expense_records 表中 2025-12-22 的记录数（应该为0）

## ❌ 错误处理

如果执行过程中出现错误：
- 所有操作会自动回滚
- 数据库状态恢复到执行前的状态
- 错误信息会记录到日志中

## 📌 重要提示

- **此脚本仅用于 2025-12-22 的数据重置**
- **如果需要重置其他日期，需要修改脚本中的 `TARGET_DATE` 变量**
- **执行前请确保数据库文件存在且可访问**
- **建议在非生产环境先测试**

---

**创建时间**: 2025-01-16  
**目标日期**: 2025-12-22  
**脚本版本**: 1.0


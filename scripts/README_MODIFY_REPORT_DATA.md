# 直接修改运行服务上的报表数据工具

## 📋 功能说明

这个工具允许你直接修改运行服务上的报表数据，包括：

1. **全局财务数据** (`financial_data` 表)
2. **分组财务数据** (`grouped_data` 表)
3. **日结数据** (`daily_data` 表)

## 🚀 快速开始

### Windows 使用

```batch
# 查看全局财务数据
scripts\modify_report_data.bat --type financial --show

# 设置全局活动资金为 100000
scripts\modify_report_data.bat --type financial --field liquid_funds --value 100000 --mode set

# 增加归属ID S01 的利息收入 5000
scripts\modify_report_data.bat --type grouped --group_id S01 --field interest --value 5000 --mode add

# 设置 2025-01-15 的全局利息收入为 1000
scripts\modify_report_data.bat --type daily --date 2025-01-15 --field interest --value 1000 --mode set
```

### Linux/Mac 使用

```bash
# 添加执行权限（首次使用）
chmod +x scripts/modify_report_data.sh

# 查看全局财务数据
./scripts/modify_report_data.sh --type financial --show

# 设置全局活动资金为 100000
./scripts/modify_report_data.sh --type financial --field liquid_funds --value 100000 --mode set

# 增加归属ID S01 的利息收入 5000
./scripts/modify_report_data.sh --type grouped --group_id S01 --field interest --value 5000 --mode add

# 设置 2025-01-15 的全局利息收入为 1000
./scripts/modify_report_data.sh --type daily --date 2025-01-15 --field interest --value 1000 --mode set
```

### 直接使用 Python

```bash
python scripts/modify_report_data.py --type financial --field liquid_funds --value 100000 --mode set
```

## 📝 参数说明

### 必需参数

- `--type`: 数据类型
  - `financial`: 全局财务数据
  - `grouped`: 分组财务数据（需要 `--group_id`）
  - `daily`: 日结数据（需要 `--date`）

### 修改参数

- `--field`: 要修改的字段名（必需，除非使用 `--show`）
- `--value`: 新值或增量值（必需，除非使用 `--show`）
- `--mode`: 修改模式（可选，默认 `set`）
  - `set`: 设置为指定值
  - `add`: 增加指定值
  - `subtract`: 减少指定值

### 条件参数

- `--group_id`: 归属ID（`grouped` 和 `daily` 类型需要）
- `--date`: 日期，格式 `YYYY-MM-DD`（`daily` 类型需要）

### 其他参数

- `--show`: 仅显示当前数据，不修改
- `--db_path`: 指定数据库文件路径（可选，默认使用环境变量 `DATA_DIR`）

## 📊 可修改的字段

### 全局财务数据 (financial_data)

- `valid_orders`: 有效订单数
- `valid_amount`: 有效订单金额
- `liquid_funds`: 活动资金
- `new_clients`: 新客户数
- `new_clients_amount`: 新客户金额
- `old_clients`: 老客户数
- `old_clients_amount`: 老客户金额
- `interest`: 利息收入
- `completed_orders`: 完成订单数
- `completed_amount`: 完成订单金额
- `breach_orders`: 违约订单数
- `breach_amount`: 违约金额
- `breach_end_orders`: 违约完成订单数
- `breach_end_amount`: 违约完成金额

### 分组财务数据 (grouped_data)

字段与全局财务数据相同，但按 `group_id` 分组。

### 日结数据 (daily_data)

- `new_clients`: 新客户数
- `new_clients_amount`: 新客户金额
- `old_clients`: 老客户数
- `old_clients_amount`: 老客户金额
- `interest`: 利息收入
- `completed_orders`: 完成订单数
- `completed_amount`: 完成订单金额
- `breach_orders`: 违约订单数
- `breach_amount`: 违约金额
- `breach_end_orders`: 违约完成订单数
- `breach_end_amount`: 违约完成金额
- `liquid_flow`: 资金流量
- `company_expenses`: 公司开销
- `other_expenses`: 其他开销

## 💡 使用示例

### 示例 1: 修正全局活动资金

```bash
# 查看当前值
python scripts/modify_report_data.py --type financial --show

# 设置为 100000
python scripts/modify_report_data.py --type financial --field liquid_funds --value 100000 --mode set

# 或者增加 5000
python scripts/modify_report_data.py --type financial --field liquid_funds --value 5000 --mode add
```

### 示例 2: 修正归属ID的利息收入

```bash
# 查看当前值
python scripts/modify_report_data.py --type grouped --group_id S01 --show

# 增加 5000
python scripts/modify_report_data.py --type grouped --group_id S01 --field interest --value 5000 --mode add

# 设置为 10000
python scripts/modify_report_data.py --type grouped --group_id S01 --field interest --value 10000 --mode set
```

### 示例 3: 修正某日的日结数据

```bash
# 查看当前值
python scripts/modify_report_data.py --type daily --date 2025-01-15 --show

# 设置全局利息收入
python scripts/modify_report_data.py --type daily --date 2025-01-15 --field interest --value 1000 --mode set

# 设置特定归属ID的利息收入
python scripts/modify_report_data.py --type daily --date 2025-01-15 --group_id S01 --field interest --value 500 --mode set
```

### 示例 4: 修正开销数据

```bash
# 设置公司开销
python scripts/modify_report_data.py --type daily --date 2025-01-15 --field company_expenses --value 2000 --mode set

# 增加其他开销
python scripts/modify_report_data.py --type daily --date 2025-01-15 --field other_expenses --value 500 --mode add
```

## ⚠️ 注意事项

1. **数据库路径**: 
   - 默认使用环境变量 `DATA_DIR` 指定的目录
   - 如果未设置，使用项目根目录
   - 可以通过 `--db_path` 参数指定

2. **数据一致性**: 
   - 修改数据后，建议检查相关统计数据的一致性
   - 可以使用 `/fix_statistics` 命令修复统计数据

3. **备份**: 
   - 修改前建议备份数据库文件
   - 数据库文件位置: `{DATA_DIR}/loan_bot.db`

4. **权限**: 
   - 确保有数据库文件的读写权限
   - 如果服务正在运行，确保数据库文件未被锁定

5. **服务状态**: 
   - 如果服务正在运行，修改会立即生效
   - 建议在服务运行时谨慎修改，避免数据冲突

## 🔍 故障排查

### 问题: 数据库文件不存在

```
❌ 数据库文件不存在: /path/to/loan_bot.db
```

**解决方案**:
1. 检查 `DATA_DIR` 环境变量是否正确设置
2. 使用 `--db_path` 参数指定正确的数据库路径
3. 确认数据库文件确实存在

### 问题: 字段不存在

```
❌ 字段名错误或不存在
```

**解决方案**:
1. 使用 `--show` 参数查看可用的字段
2. 检查字段名拼写是否正确
3. 确认该字段在对应的表中存在

### 问题: 权限不足

```
❌ 无法访问数据库文件
```

**解决方案**:
1. 检查文件权限
2. 确保有读写权限
3. 如果服务正在运行，确保数据库文件未被锁定

## 📞 更多帮助

运行以下命令查看详细帮助：

```bash
python scripts/modify_report_data.py --help
```






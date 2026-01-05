# 代码风格问题记录

## 文件大小超限（> 500行）

根据项目规范，文件不应超过500行。以下文件需要拆分：

1. **callbacks/report_callbacks_income.py** - 697行
   - **状态**: 功能内聚性高，拆分会影响多处导入
   - **建议**: 保持现状，或按功能拆分为：
     - `report_callbacks_income_view.py` - 基础视图处理（今日、本月、查询）
     - `report_callbacks_income_query.py` - 高级查询处理
     - `report_callbacks_income_page.py` - 分页处理
   - **优先级**: 低（功能内聚，拆分收益有限）

2. **utils/excel_daily_changes_sheets.py** - 669行
   - **状态**: 包含多个工作表创建函数，功能内聚性高
   - **使用情况**: 被 `utils/excel_export.py` 和 `utils/excel_export_helpers.py` 导入
   - **建议**: 
     - 选项1：保持现状（功能内聚，拆分收益有限）
     - 选项2：按工作表类型拆分为：
       - `excel_daily_changes_summary.py` - 汇总表相关（约320行）
       - `excel_daily_changes_orders.py` - 订单表相关（约260行）
       - `excel_daily_changes_records.py` - 记录表相关（约170行）
   - **优先级**: 低（功能内聚，拆分会影响多处导入）

3. **utils/order_creation_main.py** - 498行 ✅
   - **状态**: 已低于500行限制（格式化后）
   - **建议**: 无需拆分

## 代码格式问题

- 8个文件需要格式化（black）
- 160个文件需要整理导入（isort）

## 行长度问题

- 1行超过100字符限制（`db/init_tables_finance_helpers.py:32`）

## 建议

这些是长期改进任务，可以在后续重构中逐步解决。当前代码功能正常，优先级较低。


"""Excel导出辅助函数（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- excel_styles.py - Excel样式配置
- excel_orders_sheets.py - 订单总表工作表
- excel_daily_changes_sheets.py - 每日变化数据工作表
- excel_incremental_sheets.py - 增量报表工作表
"""

# 标准库
from typing import Dict, List

# 第三方库
from openpyxl import Workbook

# 本地模块
from utils.excel_daily_changes_sheets import (
    create_breach_end_orders_sheet_for_changes,
    create_completed_orders_sheet_for_changes,
    create_daily_summary_sheet_for_changes, create_expense_records_sheet,
    create_income_records_sheet, create_new_orders_sheet_for_changes)
from utils.excel_incremental_sheets import (create_incremental_expense_sheet,
                                            create_incremental_orders_sheet)
from utils.excel_orders_sheets import (create_breach_end_orders_sheet,
                                       create_breach_orders_sheet,
                                       create_chat_id_mapping_sheet,
                                       create_completed_orders_sheet,
                                       create_daily_summary_sheet,
                                       create_orders_sheet)
from utils.excel_styles import get_excel_styles

# 导出所有函数以保持向后兼容
__all__ = [
    # 样式
    "get_excel_styles",
    # 订单总表工作表
    "create_orders_sheet",
    "create_completed_orders_sheet",
    "create_breach_orders_sheet",
    "create_breach_end_orders_sheet",
    "create_daily_summary_sheet",
    "create_chat_id_mapping_sheet",
    # 每日变化数据工作表
    "create_daily_summary_sheet_for_changes",
    "create_new_orders_sheet_for_changes",
    "create_completed_orders_sheet_for_changes",
    "create_breach_end_orders_sheet_for_changes",
    "create_income_records_sheet",
    "create_expense_records_sheet",
    # 增量报表工作表
    "create_incremental_orders_sheet",
    "create_incremental_expense_sheet",
]

"""订单总表Excel - 表头模块

包含创建订单总表表头的逻辑。
"""

from openpyxl import Workbook
from openpyxl.styles import Font

from utils.excel_orders_sheets import ORDER_STATES


def create_orders_header(ws_orders, styles: dict) -> None:
    """创建订单总表表头

    Args:
        ws_orders: 工作表对象
        styles: 样式字典
    """
    # 标题
    ws_orders.merge_cells("A1:H1")
    ws_orders["A1"] = "订单总表（有效订单）"
    ws_orders["A1"].font = styles["title_font"]
    ws_orders["A1"].alignment = styles["center_align"]

    # 表头
    headers = [
        "时间",
        "订单号",
        "会员",
        "归属ID",
        "订单金额",
        "状态",
        "总利息",
        "利息记录",
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws_orders.cell(row=2, column=col_idx, value=header)
        cell.fill = styles["header_fill"]
        cell.font = styles["header_font"]
        cell.alignment = styles["center_align"]
        cell.border = styles["border"]

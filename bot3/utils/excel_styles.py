"""Excel样式配置模块

包含Excel样式定义和配置。
"""

# 第三方库
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


def get_excel_styles():
    """获取Excel样式配置"""
    return {
        "header_fill": PatternFill(
            start_color="366092", end_color="366092", fill_type="solid"
        ),
        "header_font": Font(bold=True, color="FFFFFF", size=11),
        "border": Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        ),
        "center_align": Alignment(horizontal="center", vertical="center"),
        "right_align": Alignment(horizontal="right", vertical="center"),
        "title_font": Font(bold=True, size=14),
    }

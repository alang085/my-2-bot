"""每日变更表 - 开销模块

包含生成开销变更相关内容的逻辑。
"""


def build_expense_summary(changes: dict) -> str:
    """构建开销变更汇总

    Args:
        changes: 变更数据字典

    Returns:
        str: 开销变更汇总文本
    """
    text = "<b>💸 开销变更汇总</b>\n"
    text += f"公司开销: {changes['company_expenses']:,.2f}\n"
    text += f"其他开销: {changes['other_expenses']:,.2f}\n"
    text += f"总开销: {changes['total_expenses']:,.2f}\n\n"
    return text


def build_expense_records_detail(changes: dict) -> str:
    """构建开销明细

    Args:
        changes: 变更数据字典

    Returns:
        str: 开销明细文本
    """
    text = ""
    if changes["expense_records"]:
        text += "<b>📝 开销明细（前10笔）</b>\n"
        text += "─" * 40 + "\n"
        for i, record in enumerate(changes["expense_records"][:10], 1):
            expense_type = "公司" if record.get("type") == "company" else "其他"
            amount = float(record.get("amount", 0) or 0)
            note = record.get("note", "无备注") or "无备注"
            record_date = record.get("date", "")[:10] if record.get("date") else "未知"
            text += f"{i}. {expense_type} | {amount:,.2f} | {note} | {record_date}\n"
        if len(changes["expense_records"]) > 10:
            text += f"... 还有 {len(changes['expense_records']) - 10} 笔\n"
        text += "\n"
    return text


def build_total_summary(changes: dict) -> str:
    """构建总计

    Args:
        changes: 变更数据字典

    Returns:
        str: 总计文本
    """
    text = "═" * 40 + "\n"
    text += "<b>📊 当日总计</b>\n"
    net_income = (
        changes["total_interest"]
        + changes["total_principal"]
        - changes["total_expenses"]
    )
    text += f"净收入: {net_income:,.2f}\n"
    total_income = changes["total_interest"] + changes["total_principal"]
    total_expenses = changes["total_expenses"]
    text += f"  (收入: {total_income:,.2f} - 开销: {total_expenses:,.2f})\n"
    return text

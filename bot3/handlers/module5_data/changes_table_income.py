"""每日变更表 - 收入模块

包含生成收入变更相关内容的逻辑。
"""


def build_income_summary(changes: dict) -> str:
    """构建收入变更汇总

    Args:
        changes: 变更数据字典

    Returns:
        str: 收入变更汇总文本
    """
    text = "<b>💰 收入变更汇总</b>\n"
    text += f"利息收入: {changes['total_interest']:,.2f} ({len(changes['interest_records'])} 笔)\n"
    text += f"归还本金: {changes['total_principal']:,.2f} ({len(changes['principal_records'])} 笔)\n\n"
    return text


def build_interest_records_detail(changes: dict) -> str:
    """构建利息收入明细

    Args:
        changes: 变更数据字典

    Returns:
        str: 利息收入明细文本
    """
    text = ""
    if changes["interest_records"]:
        text += "<b>💵 利息收入明细（前10笔）</b>\n"
        text += "─" * 40 + "\n"
        for i, record in enumerate(changes["interest_records"][:10], 1):
            order_id = record.get("order_id", "未知")
            amount = float(record.get("amount", 0) or 0)
            record_date = record.get("date", "")[:10] if record.get("date") else "未知"
            text += f"{i}. {order_id} | {amount:,.2f} | {record_date}\n"
        if len(changes["interest_records"]) > 10:
            text += f"... 还有 {len(changes['interest_records']) - 10} 笔\n"
        text += "\n"
    return text


def build_principal_records_detail(changes: dict) -> str:
    """构建本金归还明细

    Args:
        changes: 变更数据字典

    Returns:
        str: 本金归还明细文本
    """
    text = ""
    if changes["principal_records"]:
        text += "<b>💸 本金归还明细（前10笔）</b>\n"
        text += "─" * 40 + "\n"
        for i, record in enumerate(changes["principal_records"][:10], 1):
            order_id = record.get("order_id", "未知")
            amount = float(record.get("amount", 0) or 0)
            record_date = record.get("date", "")[:10] if record.get("date") else "未知"
            text += f"{i}. {order_id} | {amount:,.2f} | {record_date}\n"
        if len(changes["principal_records"]) > 10:
            text += f"... 还有 {len(changes['principal_records']) - 10} 笔\n"
        text += "\n"
    return text

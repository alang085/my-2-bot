"""每日变更 - 财务模块

包含获取财务相关变更的逻辑。
"""

import db_operations


async def get_finance_changes(date: str) -> dict:
    """获取财务相关变更

    Args:
        date: 日期字符串

    Returns:
        dict: 财务变更数据
    """
    # 获取当日利息收入
    interest_records = await db_operations.get_income_records(
        date, date, type="interest"
    )

    # 获取当日本金归还
    principal_records = await db_operations.get_income_records(
        date, date, type="principal_reduction"
    )

    # 获取当日开销
    expense_records = await db_operations.get_expense_records(date, date)

    total_interest = sum(
        float(record.get("amount", 0) or 0) for record in interest_records
    )
    total_principal = sum(
        float(record.get("amount", 0) or 0) for record in principal_records
    )

    company_expenses = sum(
        float(record.get("amount", 0) or 0)
        for record in expense_records
        if record.get("type") == "company"
    )
    other_expenses = sum(
        float(record.get("amount", 0) or 0)
        for record in expense_records
        if record.get("type") == "other"
    )

    return {
        "interest_records": interest_records,
        "total_interest": total_interest,
        "principal_records": principal_records,
        "total_principal": total_principal,
        "expense_records": expense_records,
        "company_expenses": company_expenses,
        "other_expenses": other_expenses,
        "total_expenses": company_expenses + other_expenses,
    }

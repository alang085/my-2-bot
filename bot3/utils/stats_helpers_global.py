"""统计辅助函数 - 全局数据更新

包含全局统计数据更新的逻辑。
"""

import logging

import db_operations

logger = logging.getLogger(__name__)


async def update_global_amount(global_amount_field: str, amount: float) -> None:
    """更新全局金额字段

    Args:
        global_amount_field: 全局金额字段名
        amount: 金额增量
    """
    if amount == 0:
        return

    try:
        result = await db_operations.update_financial_data(
            field=global_amount_field, amount=amount
        )
        if result:
            logger.debug(f"✅ 已更新全局数据: {global_amount_field} += {amount}")
        else:
            # 字段不存在或无效，记录警告但不抛出异常（兼容旧数据库）
            if "overdue" in global_amount_field:
                logger.debug(
                    f"⚠️ 跳过更新全局数据（字段不存在，兼容旧数据库）: {global_amount_field}"
                )
            else:
                logger.warning(
                    f"⚠️ 跳过更新全局数据（字段不存在或无效）: {global_amount_field}"
                )
    except Exception as e:
        # 如果是字段不存在错误，记录警告但不抛出异常（兼容旧数据库）
        error_str = str(e)
        if "无效的财务数据字段名" in error_str or "invalid" in error_str.lower():
            if "overdue" in global_amount_field:
                logger.debug(
                    f"⚠️ 跳过更新全局数据（字段不存在，兼容旧数据库）: {global_amount_field}"
                )
            else:
                logger.warning(
                    f"⚠️ 跳过更新全局数据（字段不存在）: {global_amount_field}: {e}"
                )
        else:
            logger.error(
                f"❌ 更新全局数据失败 ({global_amount_field}): {e}", exc_info=True
            )
            raise


async def update_global_count(global_count_field: str, count: int) -> None:
    """更新全局计数字段

    Args:
        global_count_field: 全局计数字段名
        count: 计数增量
    """
    if count == 0:
        return

    try:
        result = await db_operations.update_financial_data(
            global_count_field, float(count)
        )
        if result:
            logger.debug(f"✅ 已更新全局计数: {global_count_field} += {count}")
        else:
            # 字段不存在或无效，记录警告但不抛出异常（兼容旧数据库）
            if "overdue" in global_count_field:
                logger.debug(
                    f"⚠️ 跳过更新全局计数（字段不存在，兼容旧数据库）: {global_count_field}"
                )
            else:
                logger.warning(
                    f"⚠️ 跳过更新全局计数（字段不存在或无效）: {global_count_field}"
                )
    except Exception as e:
        # 如果是字段不存在错误，记录警告但不抛出异常（兼容旧数据库）
        error_str = str(e)
        if "无效的财务数据字段名" in error_str or "invalid" in error_str.lower():
            if "overdue" in global_count_field:
                logger.debug(
                    f"⚠️ 跳过更新全局计数（字段不存在，兼容旧数据库）: {global_count_field}"
                )
            else:
                logger.warning(
                    f"⚠️ 跳过更新全局计数（字段不存在）: {global_count_field}: {e}"
                )
        else:
            logger.error(
                f"❌ 更新全局计数失败 ({global_count_field}): {e}", exc_info=True
            )
            raise

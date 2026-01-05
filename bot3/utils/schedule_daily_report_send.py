"""每日报表 - 发送模块

包含发送Excel文件的逻辑。
"""

import logging
from typing import List, Optional

from telegram import Bot

from constants import ADMIN_IDS

logger = logging.getLogger(__name__)


async def send_excel_files_to_recipients(
    bot: Bot,
    all_recipients: List[int],
    orders_excel_path: Optional[str],
    changes_excel_path: Optional[str],
    report_date: str,
) -> Tuple[int, int]:
    """发送Excel文件给所有接收人

    Args:
        bot: Telegram Bot实例
        all_recipients: 接收人ID列表
        orders_excel_path: 订单总表Excel路径
        changes_excel_path: 每日变化数据Excel路径
        report_date: 报表日期

    Returns:
        Tuple[int, int]: (成功数量, 失败数量)
    """
    success_count = 0
    fail_count = 0

    for user_id in all_recipients:
        try:
            # 发送订单总表Excel
            if orders_excel_path:
                await _send_orders_excel(bot, user_id, orders_excel_path, report_date)

            # 发送每日变化数据Excel
            if changes_excel_path:
                await _send_changes_excel(bot, user_id, changes_excel_path, report_date)

            success_count += 1
            recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
            logger.info(f"每日Excel报表已发送给{recipient_type} {user_id}")
        except Exception as e:
            fail_count += 1
            recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
            logger.error(
                f"发送每日Excel报表给{recipient_type} {user_id} 失败: {e}",
                exc_info=True,
            )

    return success_count, fail_count


async def _send_orders_excel(
    bot: Bot, user_id: int, orders_excel_path: str, report_date: str
) -> None:
    """发送订单总表Excel

    Args:
        bot: Telegram Bot实例
        user_id: 用户ID
        orders_excel_path: Excel文件路径
        report_date: 报表日期
    """
    with open(orders_excel_path, "rb") as f:
        await bot.send_document(
            chat_id=user_id,
            document=f,
            filename=f"订单总表_{report_date}.xlsx",
            caption=(f"📊 订单总表 ({report_date})\n\n" f"包含所有有效订单及利息记录"),
        )


async def _send_changes_excel(
    bot: Bot, user_id: int, changes_excel_path: str, report_date: str
) -> None:
    """发送每日变化数据Excel

    Args:
        bot: Telegram Bot实例
        user_id: 用户ID
        changes_excel_path: Excel文件路径
        report_date: 报表日期
    """
    with open(changes_excel_path, "rb") as f:
        await bot.send_document(
            chat_id=user_id,
            document=f,
            filename=f"每日变化数据_{report_date}.xlsx",
            caption=(
                f"📈 每日变化数据 ({report_date})\n\n包含：\n"
                f"• 新增订单\n• 完成订单\n• 违约完成订单\n"
                f"• 收入明细（利息等）\n• 开销明细\n• 数据汇总"
            ),
        )

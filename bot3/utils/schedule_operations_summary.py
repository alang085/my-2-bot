"""每日操作汇总任务

包含每日操作汇总报告的发送功能。
"""

# 标准库
import logging

# 本地模块
import db_operations
from config import ADMIN_IDS
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


def _get_operation_type_names() -> dict:
    """获取操作类型的中文名称映射

    Returns:
        操作类型名称字典
    """
    return {
        "order_created": "订单创建",
        "order_state_change": "订单状态变更",
        "order_completed": "订单完成",
        "order_breach_end": "违约完成",
        "interest": "利息收入",
        "principal_reduction": "本金减少",
        "expense": "开销记录",
        "funds_adjustment": "资金调整",
        "other": "其他操作",
    }


def _build_summary_message_header(date: str, summary: dict) -> str:
    """构建汇总消息头部

    Args:
        date: 日期
        summary: 汇总数据

    Returns:
        消息头部文本
    """
    message = f"📊 每日操作汇总 ({date})\n"
    message += "═══════════════════════════════════════\n"
    message += f"总操作数: {summary['total_count']}\n"
    message += f"有效操作: {summary['valid_count']}\n"
    message += f"已撤销: {summary['undone_count']}\n\n"
    return message


def _build_summary_by_type(summary: dict, operation_type_names: dict) -> str:
    """构建按操作类型统计的消息

    Args:
        summary: 汇总数据
        operation_type_names: 操作类型名称映射

    Returns:
        消息文本
    """
    message = ""
    if summary.get("by_type"):
        message += "📋 按操作类型:\n"
        for op_type, count in sorted(
            summary["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            type_name = operation_type_names.get(op_type, op_type)
            message += f"  {type_name}: {count} 次\n"
        message += "\n"
    return message


def _build_summary_by_user(summary: dict) -> str:
    """构建按用户统计的消息

    Args:
        summary: 汇总数据

    Returns:
        消息文本
    """
    message = ""
    if summary.get("by_user"):
        message += "👥 操作最多的用户 (Top 5):\n"
        user_stats = sorted(
            summary["by_user"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        for user_id, count in user_stats:
            message += f"  用户 {user_id}: {count} 次\n"
    return message


async def _send_summary_to_admins(bot, message: str) -> None:
    """发送汇总消息给所有管理员

    Args:
        bot: Telegram Bot实例
        message: 消息文本
    """
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"发送操作汇总给管理员 {admin_id} 失败: {e}", exc_info=True)


async def send_daily_operations_summary(bot):
    """发送每日操作汇总报告（每天23:00执行）"""
    try:
        date = get_daily_period_date()
        logger.info(f"开始生成每日操作汇总报告 ({date})")

        summary = await db_operations.get_daily_operations_summary(date)

        if not summary or summary.get("total_count", 0) == 0:
            message = f"📊 每日操作汇总 ({date})\n\n✅ 今日无操作记录"
            await _send_summary_to_admins(bot, message)
            return

        operation_type_names = _get_operation_type_names()
        message = _build_summary_message_header(date, summary)
        message += _build_summary_by_type(summary, operation_type_names)
        message += _build_summary_by_user(summary)
        message += "\n使用 /daily_operations 查看详细操作记录"

        await _send_summary_to_admins(bot, message)
        logger.info(f"每日操作汇总报告发送完成 ({date})")

    except Exception as e:
        logger.error(f"发送每日操作汇总报告失败: {e}", exc_info=True)


async def setup_daily_operations_summary(bot):
    """设置每日操作汇总定时任务（已禁用自动发送，仅保留命令查询功能）"""
    # 不再设置定时任务，用户可以通过 /daily_operations 和 /daily_operations_summary 命令查询
    # 功能保留，可以随时查询，但不输出日志
    pass

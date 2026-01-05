"""定时播报回调处理器 - 操作模块

包含删除和切换状态相关的回调处理逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

from handlers.data_access import (delete_scheduled_broadcast_for_callback,
                                  get_scheduled_broadcast_for_callback,
                                  toggle_scheduled_broadcast_for_callback)
from utils.schedule_executor import reload_scheduled_broadcasts


async def handle_schedule_delete(
    query, data: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理删除播报回调"""
    slot = int(data.split("_")[-1])
    await delete_scheduled_broadcast_for_callback(slot)
    # 重新加载定时任务
    await reload_scheduled_broadcasts(context.bot)
    await query.answer("✅ 播报已删除")
    await query.edit_message_text(
        "✅ 定时播报已删除\n\n使用 /schedule 查看所有定时播报"
    )


async def handle_schedule_toggle(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """处理切换状态回调"""
    from callbacks.schedule_callbacks import handle_schedule_callback

    slot = int(data.split("_")[-1])
    existing = await get_scheduled_broadcast_for_callback(slot)
    if existing:
        new_status = 0 if existing["is_active"] else 1
        await toggle_scheduled_broadcast_for_callback(slot, new_status)
        # 重新加载定时任务
        await reload_scheduled_broadcasts(context.bot)
        status_text = "激活" if new_status else "停用"
        await query.answer(f"✅ 播报已{status_text}")
        # 刷新菜单
        await handle_schedule_callback(update, context)

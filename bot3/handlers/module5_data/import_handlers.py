"""订单导入处理器 - 从Excel文件导入订单"""

import logging
import os
from pathlib import Path
from typing import Any, Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from decorators import admin_required, error_handler, private_chat_only

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def _validate_and_prepare_import(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Tuple[bool, Optional[Any], Optional[Any]]:
    """验证并准备导入

    Args:
        update: Telegram更新对象
        context: 上下文对象

    Returns:
        (是否有效, 文档对象, 处理消息)
    """
    from handlers.module5_data.import_validate import validate_import_request

    if not update.message:
        return False, None, None

    is_valid, error_msg = await validate_import_request(update, context)
    if not is_valid:
        if error_msg:
            await update.message.reply_text(error_msg)
        return False, None, None

    document = update.message.document
    processing_msg = await update.message.reply_text(
        "⏳ 正在下载并处理Excel文件，请稍候..."
    )

    return True, document, processing_msg


async def _execute_import_workflow(
    document: Any, processing_msg: Any, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """执行导入工作流

    Args:
        document: 文档对象
        processing_msg: 处理消息
        context: 上下文对象
    """
    from handlers.module5_data.import_cleanup import (cleanup_temp_file,
                                                      clear_import_state)
    from handlers.module5_data.import_download import (download_excel_file,
                                                       update_download_message)
    from handlers.module5_data.import_execute import (execute_order_import,
                                                      update_import_result)

    file_path, file_size = await download_excel_file(
        document, document.file_name, context
    )
    await update_download_message(processing_msg, document.file_name, file_size)

    success, error_msg = await execute_order_import(file_path)
    await update_import_result(processing_msg, success, error_msg)

    cleanup_temp_file(file_path)
    clear_import_state(context)


async def import_orders_from_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    从上传的Excel文件导入订单

    使用方法：
    1. 发送 /import_orders 命令
    2. 然后上传Excel文件（订单报表）
    """
    is_valid, document, processing_msg = await _validate_and_prepare_import(
        update, context
    )
    if not is_valid:
        return

    try:
        await _execute_import_workflow(document, processing_msg, context)
    except Exception as e:
        logger.error(f"处理Excel文件失败: {e}", exc_info=True)
        try:
            await processing_msg.edit_text(f"❌ 处理文件失败: {str(e)}")
        except Exception:
            await update.message.reply_text(f"❌ 处理文件失败: {str(e)}")


@error_handler
@admin_required
@private_chat_only
async def import_orders_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    导入订单命令处理器

    提示用户上传Excel文件
    """
    # 设置用户状态，表示用户准备上传文件
    context.user_data["import_orders_state"] = True

    await update.message.reply_text(
        "📋 订单导入功能\n\n"
        "请上传Excel文件（订单报表）\n\n"
        "支持的格式：\n"
        "• .xlsx\n"
        "• .xls\n\n"
        "⚠️  注意：\n"
        "• 此操作会从Excel文件反推所有订单\n"
        "• 已存在的订单会被跳过\n"
        "• 请确保Excel文件包含完整的订单信息\n\n"
        "📄 Excel文件应包含以下工作表：\n"
        "• 订单总表\n"
        "• 已完成订单（可选）\n"
        "• 违约完成订单（可选）"
    )

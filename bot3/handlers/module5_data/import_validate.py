"""订单导入 - 验证模块

包含验证导入请求和文件的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes


async def validate_import_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> tuple[bool, str]:
    """验证导入请求

    Args:
        update: Telegram更新对象
        context: 上下文对象

    Returns:
        Tuple: (是否有效, 错误消息)
    """
    if not update.message:
        return False, ""

    # 检查用户是否在导入状态（通过命令触发）
    user_state = context.user_data.get("import_orders_state")
    if not user_state:
        # 如果用户没有发送命令，忽略文档上传
        return False, ""

    # 检查是否有文档附件
    if not update.message.document:
        error_msg = (
            "📋 请上传Excel文件（订单报表）\n\n"
            "使用方法：\n"
            "1. 发送 /import_orders 命令\n"
            "2. 然后上传Excel文件（.xlsx格式）\n\n"
            "⚠️  注意：此操作会从Excel文件反推所有订单并保存到数据库"
        )
        return False, error_msg

    document = update.message.document

    # 检查文件类型
    if not document.file_name:
        return False, "❌ 无法识别文件类型"

    if not document.file_name.endswith((".xlsx", ".xls")):
        return False, "❌ 请上传Excel文件（.xlsx或.xls格式）"

    return True, ""

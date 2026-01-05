"""订单导入 - 清理模块

包含清理临时文件和状态的逻辑。
"""

import logging
import os
from pathlib import Path

from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def cleanup_temp_file(file_path: Path) -> None:
    """清理临时文件

    Args:
        file_path: 文件路径
    """
    try:
        os.remove(file_path)
        logger.info(f"已删除临时文件: {file_path}")
    except Exception as e:
        logger.warning(f"删除临时文件失败: {e}")


def clear_import_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    """清除导入状态

    Args:
        context: 上下文对象
    """
    context.user_data.pop("import_orders_state", None)

"""回调处理策略

使用策略模式简化回调处理逻辑。
"""

from typing import Callable, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes


# 回调数据键名常量
class CallbackKeys:
    """回调数据键名常量"""

    ACTION = "action"
    TYPE = "type"
    ID = "id"
    PAGE = "page"
    VIEW = "view"


def create_callback_handler_map(
    handlers: Dict[str, Callable],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE, Dict], Optional[bool]]:
    """创建回调处理器映射

    Args:
        handlers: 处理器字典，键为回调数据值，值为处理函数

    Returns:
        统一的回调处理函数
    """

    async def handle_callback(
        update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: Dict
    ) -> Optional[bool]:
        """统一的回调处理函数

        Args:
            update: Telegram更新对象
            context: 上下文对象
            callback_data: 回调数据字典

        Returns:
            处理结果，如果未找到处理器则返回None
        """
        # 从callback_data中提取键值
        key = _extract_callback_key(callback_data)
        handler = handlers.get(key)
        if handler:
            return await handler(update, context, callback_data)
        return None

    return handle_callback


def _extract_callback_key(callback_data: Dict) -> str:
    """从回调数据中提取键值

    Args:
        callback_data: 回调数据字典

    Returns:
        键值字符串
    """
    # 优先使用action，然后是type，最后是第一个非空值
    return (
        callback_data.get(CallbackKeys.ACTION)
        or callback_data.get(CallbackKeys.TYPE)
        or next((v for v in callback_data.values() if v), "")
    )

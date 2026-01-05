"""订单更新 - 获取现有订单模块

包含获取现有订单信息的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def fetch_existing_order(cursor, chat_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """获取现有订单信息

    Args:
        cursor: 数据库游标
        chat_id: 聊天ID

    Returns:
        Tuple[bool, Optional[Dict]]: (是否成功, 订单字典)
    """
    cursor.execute(
        "SELECT * FROM orders WHERE chat_id = ? AND state NOT IN (?, ?)",
        (chat_id, "end", "breach_end"),
    )
    order_row = cursor.fetchone()

    if not order_row:
        logger.warning(f"订单不存在（chat_id: {chat_id}）")
        return False, None

    return True, dict(order_row)

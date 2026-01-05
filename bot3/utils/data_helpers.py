"""数据操作辅助模块

包含数据一致性检查和安全执行相关的辅助函数。
"""

# 标准库
import logging
from typing import Any, Callable, List, Optional, Tuple

from telegram import Update

logger = logging.getLogger(__name__)


def check_data_consistency(params: "DataConsistencyParams") -> None:
    """检查数据一致性并记录不匹配

    Args:
        params: 数据一致性参数
    """
    from utils.data_consistency_data import DataConsistencyParams

    diff = abs(params.stats_value - params.income_value)
    if diff > params.tolerance:
        params.mismatches.append(params.field_name)
        params.output_lines.append(f"⚠️ 不一致! {params.field_name}:")
        params.output_lines.append(f"  {params.stats_label}: {params.stats_value:.2f}")
        params.output_lines.append(
            f"  {params.income_label}: {params.income_value:.2f}"
        )
        params.output_lines.append(f"  差异: {diff:.2f}")
        params.output_lines.append("")


async def safe_execute_with_error_handling(
    func: Callable,
    update: Optional[Update] = None,
    error_message: str = "操作失败",
    log_error: bool = True,
    *args,
    **kwargs,
) -> Tuple[Any, Optional[str]]:
    """统一的安全执行函数，带错误处理

    Args:
        func: 要执行的函数（可以是同步或异步）
        update: Telegram 更新对象（可选，用于发送错误消息）
        error_message: 错误消息模板
        log_error: 是否记录错误日志
        *args: 传递给函数的参数
        **kwargs: 传递给函数的关键字参数

    Returns:
        (函数返回值, 错误消息) 如果成功返回 (result, None)，失败返回 (None, error_msg)
    """
    try:
        import asyncio

        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        error_msg = f"⚠️ {error_message}: {str(e)}"
        if log_error:
            logger.error(f"{error_message} - {func.__name__}: {e}", exc_info=True)

        # 尝试发送错误消息给用户
        if update:
            try:
                from utils.callback_helpers import safe_reply_text

                await safe_reply_text(update, error_msg)
            except Exception as send_error:
                if log_error:
                    logger.error(f"发送错误消息失败: {send_error}")

        return None, error_msg

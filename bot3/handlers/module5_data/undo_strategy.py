"""撤销操作策略模式

使用策略模式简化撤销操作的类型分发逻辑。
"""

from typing import Callable, Dict, Tuple

from handlers.module5_data.undo_helpers import (
    _build_unsupported_undo_message, _execute_undo_expense,
    _execute_undo_interest, _execute_undo_order_operations,
    _execute_undo_principal_reduction)

# 撤销操作策略映射表
UNDO_STRATEGIES: Dict[str, Callable] = {
    "interest": _execute_undo_interest,
    "principal_reduction": _execute_undo_principal_reduction,
    "expense": _execute_undo_expense,
    "order_completed": lambda op_data: _execute_undo_order_operations(
        "order_completed", op_data
    ),
    "order_breach_end": lambda op_data: _execute_undo_order_operations(
        "order_breach_end", op_data
    ),
    "order_created": lambda op_data: _execute_undo_order_operations(
        "order_created", op_data
    ),
    "order_state_change": lambda op_data: _execute_undo_order_operations(
        "order_state_change", op_data
    ),
}


async def execute_undo_by_type_strategy(
    operation_type: str, operation_data: Dict
) -> Tuple[bool, str, str]:
    """根据操作类型执行撤销（使用策略模式）

    Args:
        operation_type: 操作类型
        operation_data: 操作数据

    Returns:
        Tuple[是否成功, 中文消息, 英文消息]
    """
    strategy = UNDO_STRATEGIES.get(operation_type)
    if strategy:
        return await strategy(operation_data)
    return _build_unsupported_undo_message(operation_type)

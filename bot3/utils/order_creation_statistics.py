"""订单创建辅助函数 - 统计更新模块

包含订单创建后统计更新的逻辑。
"""

import logging
from typing import Any, Dict

from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def update_statistics_for_new_order(
    initial_state: str,
    amount: float,
    group_id: str,
    customer: str,
    is_historical: bool,
) -> None:
    """更新新订单的统计数据

    Args:
        initial_state: 初始状态
        amount: 订单金额
        group_id: 归属ID
        customer: 客户类型
        is_historical: 是否为历史订单
    """
    is_initial_breach = initial_state == "breach"

    # 更新订单统计
    # 历史违约订单：只更新全局和分组统计，不更新日结统计
    if is_initial_breach:
        if is_historical:
            # 历史违约订单：跳过日结更新
            await update_all_stats("breach", amount, 1, group_id, skip_daily=True)
        else:
            # 非历史违约订单：正常更新（包括日结）
            await update_all_stats("breach", amount, 1, group_id)
    else:
        await update_all_stats("valid", amount, 1, group_id)

    # 非历史订单才扣款和更新客户统计
    if not is_historical:
        # 扣除流动资金
        await update_liquid_capital(-amount)

        # 客户统计
        client_field = "new_clients" if customer == "A" else "old_clients"
        await update_all_stats(client_field, amount, 1, group_id)

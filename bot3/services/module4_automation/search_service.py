"""搜索服务 - 封装搜索相关的业务逻辑"""

import logging
from typing import Dict, List

import db_operations

logger = logging.getLogger(__name__)


class SearchService:
    """搜索业务服务"""

    @staticmethod
    async def search_orders(criteria: Dict) -> List[Dict]:
        """搜索订单

        Args:
            criteria: 搜索条件字典，包含：
                - order_id: 订单ID（可选）
                - customer: 客户类型（可选）
                - state: 订单状态（可选）
                - group_id: 归属ID（可选）
                - start_date: 开始日期（可选）
                - end_date: 结束日期（可选）

        Returns:
            订单列表
        """
        return await db_operations.search_orders_advanced(criteria)

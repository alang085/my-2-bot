"""统计修复服务 - 封装统计修复相关的业务逻辑"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import db_operations

logger = logging.getLogger(__name__)


class StatsService:
    """统计修复业务服务"""

    @staticmethod
    async def fix_statistics(
        group_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """修复统计数据

        Args:
            group_id: 归属ID（可选，如果提供则只修复该归属的统计）

        Returns:
            Tuple[success, result_dict]:
                - success: 是否成功
                - result_dict: 结果字典，包含修复的统计信息
        """
        try:
            # 调用现有的修复函数
            result = await db_operations.fix_statistics(group_id)
            return True, result
        except Exception as e:
            logger.error(f"修复统计数据失败: {e}", exc_info=True)
            return False, {"error": str(e)}

    @staticmethod
    async def fix_income_statistics(
        group_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """修复收入统计

        Args:
            group_id: 归属ID（可选，如果提供则只修复该归属的统计）

        Returns:
            Tuple[success, result_dict]:
                - success: 是否成功
                - result_dict: 结果字典，包含修复的统计信息
        """
        try:
            # 调用现有的修复函数
            result = await db_operations.fix_income_statistics(group_id)
            return True, result
        except Exception as e:
            logger.error(f"修复收入统计失败: {e}", exc_info=True)
            return False, {"error": str(e)}

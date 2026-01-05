"""报表服务 - 封装报表相关的业务逻辑"""

import logging
from datetime import datetime
from typing import Dict, Optional

import pytz

import db_operations

logger = logging.getLogger(__name__)


class ReportService:
    """报表业务服务"""

    @staticmethod
    async def _update_group_current_data_with_global_funds(current_data: Dict) -> None:
        """更新归属当前数据的全局现金余额

        Args:
            current_data: 当前数据字典
        """
        try:
            global_financial_data = await db_operations.get_financial_data()
            if global_financial_data:
                current_data["liquid_funds"] = global_financial_data.get(
                    "liquid_funds", 0.0
                )
        except Exception as e:
            logger.error(f"获取全局数据失败: {e}", exc_info=True)
            current_data["liquid_funds"] = current_data.get("liquid_funds", 0.0)

    async def generate_report_text(
        period_type: str,
        start_date: str,
        end_date: str,
        group_id: Optional[str] = None,
        show_expenses: bool = True,
    ) -> str:
        """生成报表文本

        报表数据来源说明：
        - 全局报表（group_id=None）：
          * current_data: financial_data表（全局统计数据）
          * stats: daily_data表按日期范围汇总，group_id=NULL（全局日结数据）

        - 归属报表（group_id有值）：
          * current_data: grouped_data表（该归属ID的累计统计数据）
          * stats: daily_data表按日期范围汇总，group_id=指定值（该归属ID的日结数据）
          * 开销数据：使用全局数据（开销不按归属ID存储）
          * 现金余额：使用全局数据（现金余额是全局的）

        数据一致性保证：
        - grouped_data的数据应该等于该归属ID在daily_data表中的数据累计
        - 所有统计数据应该与income_records表中的明细数据一致
        """
        from services.module5_data.report_build import build_report_text
        from services.module5_data.report_data import (get_report_current_data,
                                                       get_report_stats)

        current_data = await get_report_current_data(group_id)
        stats = await get_report_stats(start_date, end_date, group_id)

        if group_id:
            await ReportService._update_group_current_data_with_global_funds(
                current_data
            )

        report = build_report_text(
            period_type,
            start_date,
            end_date,
            group_id,
            current_data,
            stats,
            show_expenses,
        )

        return report

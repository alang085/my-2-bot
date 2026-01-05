"""每日报表 - 日期处理模块

包含获取日切日期的逻辑。
"""

import logging
from datetime import datetime, timedelta

import pytz

logger = logging.getLogger(__name__)


def get_report_date() -> str:
    """获取报表日期

    如果当前时间在23:00之后，统计今天的数据；否则统计昨天的数据

    Returns:
        str: 报表日期（格式：YYYY-MM-DD）
    """
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)

    # 如果当前时间在23:00之后，统计今天的数据；否则统计昨天的数据
    if now.hour >= 23:
        # 23:00之后，统计今天的数据
        report_date = now.strftime("%Y-%m-%d")
    else:
        # 23:00之前，统计昨天的数据
        yesterday = now - timedelta(days=1)
        report_date = yesterday.strftime("%Y-%m-%d")

    return report_date

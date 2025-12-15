"""增量报表生成器"""
# 标准库
import logging
from typing import Dict, List
from datetime import datetime
import pytz

# 本地模块
import db_operations

logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


async def prepare_incremental_data(baseline_date: str, end_date: str = None) -> Dict:
    """准备增量数据
    
    Args:
        baseline_date: 基准日期（起始日期）
        end_date: 结束日期（可选，默认为当前日期）
    """
    try:
        if not end_date:
            end_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        
        # 获取增量订单及其详细信息
        orders_data = await db_operations.get_incremental_orders_with_details(baseline_date)
        
        # 过滤出end_date之前的数据（包括end_date当天）
        filtered_orders = []
        for order in orders_data:
            order_date = order.get('date', '')[:10] if order.get('date') else ''
            created_at = order.get('created_at', '')[:10] if order.get('created_at') else ''
            # 使用创建日期或订单日期中较晚的作为判断依据
            check_date = created_at if created_at and created_at > order_date else order_date
            if check_date and check_date <= end_date:
                filtered_orders.append(order)
        
        # 获取增量开销记录
        expense_records = await db_operations.get_expense_records(baseline_date, end_date)
        
        return {
            'orders': filtered_orders,
            'expenses': expense_records,
            'baseline_date': baseline_date,
            'end_date': end_date,
            'current_date': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        }
    except Exception as e:
        logger.error(f"准备增量数据失败: {e}", exc_info=True)
        return {
            'orders': [],
            'expenses': [],
            'baseline_date': baseline_date,
            'end_date': end_date,
            'current_date': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        }


async def get_or_create_baseline_date() -> str:
    """获取或创建基准日期"""
    try:
        # 检查基准日期是否存在
        exists = await db_operations.check_baseline_exists()
        
        if not exists:
            # 创建基准日期（使用当前日期）
            current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
            await db_operations.save_baseline_date(current_date)
            logger.info(f"基准日期已创建: {current_date}")
            return current_date
        else:
            # 获取基准日期
            baseline_date = await db_operations.get_baseline_date()
            if baseline_date:
                return baseline_date
            else:
                # 如果获取失败，创建新的基准日期
                current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
                await db_operations.save_baseline_date(current_date)
                logger.info(f"基准日期已重新创建: {current_date}")
                return current_date
    except Exception as e:
        logger.error(f"获取或创建基准日期失败: {e}", exc_info=True)
        # 返回当前日期作为默认值
        return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')


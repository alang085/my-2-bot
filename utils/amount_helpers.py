"""金额处理相关工具函数"""
import re
from typing import Optional, List, Dict


def parse_amount(text: str) -> Optional[float]:
    """
    解析金额文本，支持多种格式
    例如: "20万" -> 200000, "20.5万" -> 205000, "200000" -> 200000
    """
    text = text.strip().replace(',', '')
    
    # 匹配"万"单位
    match = re.match(r'^(\d+(?:\.\d+)?)\s*万$', text)
    if match:
        return float(match.group(1)) * 10000
    
    # 匹配纯数字
    match = re.match(r'^(\d+(?:\.\d+)?)$', text)
    if match:
        return float(match.group(1))
    
    return None


def select_orders_by_amount(orders: List[Dict], target_amount: float) -> List[Dict]:
    """
    使用贪心算法从订单列表中选择订单，使得总金额尽可能接近目标金额
    返回选中的订单列表
    """
    if not orders or target_amount <= 0:
        return []
    
    # 按金额降序排序
    sorted_orders = sorted(orders, key=lambda x: x.get('amount', 0), reverse=True)
    
    selected = []
    current_total = 0.0
    
    for order in sorted_orders:
        order_amount = order.get('amount', 0)
        if order_amount <= 0:
            continue  # 跳过金额为0或负数的订单
        
        if current_total + order_amount <= target_amount:
            selected.append(order)
            current_total += order_amount
        elif current_total < target_amount and current_total + order_amount - target_amount < target_amount * 0.1:
            # 如果超过目标金额但差额小于10%，仍然选择（允许小幅超过）
            selected.append(order)
            current_total += order_amount
            break  # 达到目标后停止
    
    return selected


def distribute_orders_evenly_by_weekday(orders: List[Dict], target_total_amount: float) -> List[Dict]:
    """
    从周一到周日的有效订单中，均匀地选择订单，使得总金额接近目标金额
    返回选中的订单列表
    """
    from constants import WEEKDAY_GROUP
    
    if not orders or target_total_amount <= 0:
        return []
    
    # 按星期分组
    weekday_orders = {}
    for weekday_name in WEEKDAY_GROUP.values():
        weekday_orders[weekday_name] = []
    
    for order in orders:
        weekday_group = order.get('weekday_group')
        if weekday_group in weekday_orders:
            weekday_orders[weekday_group].append(order)
    
    # 计算每天的目标金额
    daily_target = target_total_amount / 7
    
    selected_orders = []
    
    # 对每天使用贪心算法选择订单
    for weekday_name in ['一', '二', '三', '四', '五', '六', '日']:
        day_orders = weekday_orders.get(weekday_name, [])
        if day_orders:
            day_selected = select_orders_by_amount(day_orders, daily_target)
            selected_orders.extend(day_selected)
    
    return selected_orders


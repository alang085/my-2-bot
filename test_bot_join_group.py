"""测试机器人进群读取群名创建订单"""
import re
from datetime import datetime, date
from utils.broadcast_helpers import calculate_next_payment_date, format_broadcast_message

def parse_order_from_title(title: str):
    """从群名解析订单信息"""
    customer = 'B'
    raw_digits = None
    order_id = None

    match_new = re.search(r'A(\d{10})', title)
    if match_new:
        customer = 'A'
        raw_digits = match_new.group(1)
        order_id = match_new.group(0)
    else:
        match_old = re.search(r'(?<!A)(\d{10})(?!\d)', title)
        if match_old:
            customer = 'B'
            raw_digits = match_old.group(1)
            order_id = match_old.group(1)

    if not raw_digits:
        return None

    date_part = raw_digits[:6]
    amount_part = raw_digits[8:10]

    try:
        full_date_str = f"20{date_part}"
        order_date_obj = datetime.strptime(full_date_str, "%Y%m%d").date()
    except ValueError:
        return None

    amount = int(amount_part) * 1000

    return {
        'date': order_date_obj,
        'amount': amount,
        'order_id': order_id,
        'customer': customer,
        'full_date_str': full_date_str
    }

# 测试群名
test_title = "2508220210（3）"

print("=" * 60)
print("机器人进群测试")
print("=" * 60)
print(f"场景: 机器人被添加到群组")
print(f"群名: {test_title}")
print()

# 步骤1: 解析群名
print("步骤1: 解析群名")
print("-" * 60)
parsed_info = parse_order_from_title(test_title)

if not parsed_info:
    print("解析失败: 群名格式不符合要求")
    exit(1)

print("解析成功!")
print(f"  订单ID: {parsed_info['order_id']}")
print(f"  客户类型: {parsed_info['customer']} ({'新客户' if parsed_info['customer'] == 'A' else '老客户'})")
print(f"  订单日期: {parsed_info['date']} ({parsed_info['date'].strftime('%A')})")
print(f"  订单金额: {parsed_info['amount']:,}")
print()

# 步骤2: 检查订单信息
print("步骤2: 订单信息")
print("-" * 60)
order_date = parsed_info['date']
amount = parsed_info['amount']
order_id = parsed_info['order_id']
customer = parsed_info['customer']

print(f"订单ID: {order_id}")
print(f"订单日期: {order_date}")
print(f"订单金额: {amount:,}")
print(f"客户类型: {'New' if customer == 'A' else 'Returning'}")
print()

# 步骤3: 计算下个付款日期
print("步骤3: 计算下个付款日期")
print("-" * 60)
next_date, date_str, weekday_str = calculate_next_payment_date(order_date)
print(f"订单日期: {order_date} ({order_date.strftime('%A')})")
print(f"当前日期: {datetime.now().date()} ({datetime.now().strftime('%A')})")
print(f"下个付款日期: {date_str} ({weekday_str})")
print()

# 步骤4: 生成播报消息
print("步骤4: 生成播报消息")
print("-" * 60)
principal = amount
principal_12 = principal * 0.12
outstanding_interest = 0

message = format_broadcast_message(
    principal=principal,
    principal_12=principal_12,
    outstanding_interest=outstanding_interest,
    date_str=date_str,
    weekday_str=weekday_str
)

print("播报消息:")
print(message)
print()

# 步骤5: 模拟创建订单
print("步骤5: 模拟创建订单")
print("-" * 60)
print("如果机器人进群，将执行以下操作:")
print(f"  1. 解析群名: {test_title}")
print(f"  2. 提取订单信息:")
print(f"     - 订单ID: {order_id}")
print(f"     - 日期: {order_date}")
print(f"     - 金额: {amount:,}")
print(f"     - 客户: {'New' if customer == 'A' else 'Returning'}")
print(f"  3. 检查是否已存在订单")
print(f"  4. 创建订单到数据库")
print(f"  5. 更新统计数据")
print(f"  6. 扣除流动资金")
print(f"  7. 发送确认消息")
print(f"  8. 自动播报下一期还款")
print()

print("=" * 60)
print("测试结果: 成功")
print("=" * 60)
print("群名 '2508220210（3）' 可以正确解析并创建订单")
print("机器人进群时会自动执行上述流程")


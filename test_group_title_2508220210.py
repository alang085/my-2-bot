"""测试群名解析: 2508220210（3）"""
import re
from datetime import datetime

def parse_order_from_title(title: str):
    """从群名解析订单信息（更新后的版本）"""
    customer = 'B'
    raw_digits = None
    order_id = None

    # Check for New Customer (A + 10 digits, 可以在任何位置)
    match_new = re.search(r'A(\d{10})', title)
    if match_new:
        customer = 'A'
        raw_digits = match_new.group(1)
        order_id = match_new.group(0)
    else:
        # Check for Old Customer (10 consecutive digits, 可以在任何位置)
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
print("测试群名解析")
print("=" * 60)
print(f"群名: {test_title}")
print()

# 解析群名
result = parse_order_from_title(test_title)

if result:
    print("解析成功!")
    print(f"订单ID: {result['order_id']}")
    print(f"客户类型: {result['customer']} ({'新客户' if result['customer'] == 'A' else '老客户'})")
    print(f"订单日期: {result['date']} ({result['date'].strftime('%A')})")
    print(f"订单金额: {result['amount']:,}")
    print(f"完整日期字符串: {result['full_date_str']}")
    print()
    
    # 计算下个付款日期
    from datetime import timedelta
    from utils.broadcast_helpers import calculate_next_payment_date, format_broadcast_message
    
    next_date, date_str, weekday_str = calculate_next_payment_date(result['date'])
    print("=" * 60)
    print("下个付款日期")
    print("=" * 60)
    print(f"订单日期: {result['date']} ({result['date'].strftime('%A')})")
    print(f"当前日期: {datetime.now().date()} ({datetime.now().strftime('%A')})")
    print(f"下个付款日期: {date_str} ({weekday_str})")
    print()
    
    # 生成播报消息
    principal = result['amount']
    principal_12 = principal * 0.12
    outstanding_interest = 0
    
    message = format_broadcast_message(
        principal=principal,
        principal_12=principal_12,
        outstanding_interest=outstanding_interest,
        date_str=date_str,
        weekday_str=weekday_str
    )
    
    print("=" * 60)
    print("播报消息")
    print("=" * 60)
    print(message)
    print("=" * 60)
else:
    print("解析失败!")
    print("群名格式不符合要求")
    print()
    print("要求:")
    print("- 老客户: 群名中包含10位连续数字")
    print("- 新客户: 群名中包含 A + 10位连续数字")
    print()
    print("当前群名分析:")
    print(f"  长度: {len(test_title)}")
    print(f"  包含数字: {bool(re.search(r'\d', test_title))}")
    digits = re.findall(r'\d+', test_title)
    print(f"  所有数字段: {digits}")
    for i, d in enumerate(digits):
        print(f"    段 {i+1}: {d} (长度: {len(d)})")
    print()
    print("建议:")
    if any(len(d) == 10 for d in digits):
        print("  - 群名中包含10位数字，应该可以解析")
        print("  - 请检查正则表达式是否正确")
    else:
        print("  - 群名中没有10位连续数字")
        print("  - 请确保群名中包含10位连续数字")


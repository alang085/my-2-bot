"""测试历史订单处理"""
from datetime import date
from constants import HISTORICAL_THRESHOLD_DATE

print("=" * 60)
print("历史订单处理测试")
print("=" * 60)

threshold_date = date(*HISTORICAL_THRESHOLD_DATE)
print(f"历史订单阈值日期: {threshold_date}")
print()

# 测试不同日期的订单
test_dates = [
    ("2025-11-27", date(2025, 11, 27)),  # 历史订单
    ("2025-11-28", date(2025, 11, 28)),  # 边界日期（正常订单）
    ("2025-11-29", date(2025, 11, 29)),  # 正常订单
    ("2025-08-22", date(2025, 8, 22)),   # 历史订单
]

print("订单日期判断:")
print("-" * 60)
for date_str, order_date in test_dates:
    is_historical = order_date < threshold_date
    status = "历史订单" if is_historical else "正常订单"
    
    print(f"订单日期: {date_str}")
    print(f"  判断: {status}")
    if is_historical:
        print(f"  处理: 不扣款，仅更新统计，不播报")
    else:
        print(f"  处理: 扣款，更新统计，自动播报")
    print()

print("=" * 60)
print("历史订单处理规则")
print("=" * 60)
print("1. 订单日期 < 2025-11-28 → 历史订单")
print("   - 不扣除流动资金")
print("   - 仅更新统计数据")
print("   - 不发送播报消息")
print()
print("2. 订单日期 >= 2025-11-28 → 正常订单")
print("   - 扣除流动资金")
print("   - 更新统计数据")
print("   - 自动发送播报消息")
print("=" * 60)


"""简单测试收入明细格式"""
import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '.')

async def test_format():
    """测试格式化函数"""
    from handlers.income_handlers import format_income_detail
    
    # 测试记录
    test_record = {
        'amount': 7400.00,
        'order_id': '2511100615',
        'created_at': '2024-12-02T17:30:45+08:00',
        'type': 'principal_reduction',
        'customer': None,
        'group_id': None,
        'note': None
    }
    
    result = await format_income_detail(test_record)
    print("格式化结果:", result)
    
    # 验证
    assert "7,400.00" in result
    assert "2511100615" in result
    assert "17:30:45" in result
    print("✅ 格式化测试通过")

async def test_report():
    """测试报表生成"""
    import db_operations
    from handlers.income_handlers import generate_income_report
    from utils.date_helpers import get_daily_period_date
    
    date = get_daily_period_date()
    print(f"查询日期: {date}")
    
    records = await db_operations.get_income_records(date, date)
    print(f"记录数量: {len(records)}")
    
    if records:
        report, has_more, total_pages, current_type = await generate_income_report(
            records, date, date, f"测试报表 ({date})", page=1
        )
        print(f"\n报表预览（前500字符）:")
        print(report[:500])
        print(f"\n分页信息: has_more={has_more}, total_pages={total_pages}, current_type={current_type}")
        print("✅ 报表生成测试通过")
    else:
        print("⚠️ 无记录，跳过报表测试")

if __name__ == "__main__":
    print("开始测试...")
    asyncio.run(test_format())
    print()
    asyncio.run(test_report())
    print("\n测试完成！")


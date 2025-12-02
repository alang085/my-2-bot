"""直接测试收入明细功能"""
import asyncio
import sys
sys.path.insert(0, '.')

async def main():
    print("开始测试...")
    
    # 测试格式化
    from handlers.income_handlers import format_income_detail
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
    print(f"格式化结果: {result}")
    
    # 测试报表生成
    import db_operations
    from handlers.income_handlers import generate_income_report
    from utils.date_helpers import get_daily_period_date
    
    date = get_daily_period_date()
    print(f"\n查询日期: {date}")
    
    # 创建一些测试数据
    print("\n创建测试数据...")
    for i in range(25):
        await db_operations.record_income(
            date=date,
            type='interest',
            amount=100.00 + i * 10,
            order_id=f'TEST{i:04d}',
            note=f'测试记录 {i+1}'
        )
    print("✅ 测试数据创建完成")
    
    # 获取记录
    records = await db_operations.get_income_records(date, date, type='interest')
    print(f"\n利息记录数: {len(records)}")
    
    # 测试分页
    print("\n测试第1页:")
    report1, has_more1, total_pages1, current_type1 = await generate_income_report(
        records, date, date, f"利息收入 ({date})", page=1, income_type='interest'
    )
    print(f"总页数: {total_pages1}, 是否有更多: {has_more1}")
    print(f"报表预览:\n{report1[:400]}...")
    
    if total_pages1 > 1:
        print("\n测试第2页:")
        report2, has_more2, total_pages2, current_type2 = await generate_income_report(
            records, date, date, f"利息收入 ({date})", page=2, income_type='interest'
        )
        print(f"总页数: {total_pages2}, 是否有更多: {has_more2}")
        print(f"报表预览:\n{report2[:400]}...")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


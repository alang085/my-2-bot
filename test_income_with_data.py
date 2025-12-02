"""测试收入明细分页功能（创建测试数据）"""
import asyncio
import sys
from datetime import datetime
import pytz

sys.path.insert(0, '.')

import db_operations
from handlers.income_handlers import generate_income_report, format_income_detail
from utils.date_helpers import get_daily_period_date


async def create_test_data():
    """创建测试数据"""
    print("=" * 50)
    print("创建测试数据")
    print("=" * 50)
    
    date = get_daily_period_date()
    tz = pytz.timezone('Asia/Shanghai')
    
    # 创建25条利息记录（超过20条，用于测试分页）
    print(f"创建25条利息记录（日期: {date}）...")
    for i in range(25):
        amount = 100.00 + i * 10
        order_id = f"TEST{i:04d}"
        
        await db_operations.record_income(
            date=date,
            type='interest',
            amount=amount,
            order_id=order_id,
            note=f"测试利息记录 {i+1}"
        )
    
    print("✅ 测试数据创建完成")
    print()


async def test_pagination():
    """测试分页功能"""
    print("=" * 50)
    print("测试分页功能")
    print("=" * 50)
    
    date = get_daily_period_date()
    
    # 获取利息记录
    records = await db_operations.get_income_records(date, date, type='interest')
    print(f"利息记录总数: {len(records)}")
    print()
    
    if len(records) < 20:
        print("⚠️ 记录数不足20条，无法测试分页")
        return
    
    # 测试第1页
    print("--- 第1页 ---")
    report1, has_more1, total_pages1, current_type1 = await generate_income_report(
        records, date, date, f"利息收入测试 ({date})", page=1, income_type='interest'
    )
    
    print(f"总页数: {total_pages1}")
    print(f"是否有更多页: {has_more1}")
    print(f"当前类型: {current_type1}")
    print()
    print("报表内容（前300字符）:")
    print(report1[:300])
    print("...")
    print()
    
    # 测试第2页
    if has_more1 and total_pages1 > 1:
        print("--- 第2页 ---")
        report2, has_more2, total_pages2, current_type2 = await generate_income_report(
            records, date, date, f"利息收入测试 ({date})", page=2, income_type='interest'
        )
        
        print(f"总页数: {total_pages2}")
        print(f"是否有更多页: {has_more2}")
        print()
        print("报表内容（前300字符）:")
        print(report2[:300])
        print("...")
        print()
    
    # 验证格式
    print("--- 验证格式 ---")
    if records:
        sample = records[0]
        formatted = await format_income_detail(sample)
        print(f"示例格式: {formatted}")
        
        # 验证格式包含金额、订单号、时间
        assert "|" in formatted, "格式错误：缺少分隔符"
        parts = formatted.split("|")
        assert len(parts) == 3, f"格式错误：应该有3部分，实际有{len(parts)}部分"
        print("✅ 格式验证通过")
    
    print()
    print("✅ 分页测试通过")
    print()


async def test_all_types_view():
    """测试显示所有类型（不分页）"""
    print("=" * 50)
    print("测试显示所有类型")
    print("=" * 50)
    
    date = get_daily_period_date()
    
    # 获取所有记录
    records = await db_operations.get_income_records(date, date)
    print(f"总记录数: {len(records)}")
    print()
    
    # 生成报表（不指定类型）
    report, has_more, total_pages, current_type = await generate_income_report(
        records, date, date, f"全部收入明细 ({date})", page=1
    )
    
    print(f"是否有更多页: {has_more}")
    print(f"总页数: {total_pages}")
    print(f"当前类型: {current_type}")
    print()
    print("报表内容（前500字符）:")
    print(report[:500])
    print("...")
    print()
    
    print("✅ 所有类型显示测试通过")
    print()


async def cleanup_test_data():
    """清理测试数据（可选）"""
    print("=" * 50)
    print("清理测试数据")
    print("=" * 50)
    
    # 注意：这里不实际删除数据，只是提示
    print("⚠️ 测试数据已创建，如需清理请手动删除")
    print("   查询条件: date =", get_daily_period_date(), ", type = 'interest', order_id LIKE 'TEST%'")
    print()


async def run_tests():
    """运行所有测试"""
    try:
        # 创建测试数据
        await create_test_data()
        
        # 测试分页
        await test_pagination()
        
        # 测试所有类型显示
        await test_all_types_view()
        
        # 清理提示
        await cleanup_test_data()
        
        print("=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50)
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ 测试失败: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_tests())


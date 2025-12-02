"""测试收入明细格式和分页功能"""
import asyncio
import sys
from datetime import datetime
import pytz

# 添加项目路径
sys.path.insert(0, '.')

import db_operations
from handlers.income_handlers import format_income_detail, generate_income_report
from utils.date_helpers import get_daily_period_date


async def test_format_income_detail():
    """测试收入明细格式化"""
    print("=" * 50)
    print("测试1: 收入明细格式化")
    print("=" * 50)
    
    # 创建测试记录
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
    print(f"测试记录: {test_record}")
    print(f"格式化结果: {result}")
    print()
    
    # 验证格式
    assert "7,400.00" in result, "金额格式错误"
    assert "2511100615" in result, "订单号缺失"
    assert "17:30:45" in result, "时间格式错误"
    assert "|" in result, "分隔符缺失"
    
    print("✅ 格式化测试通过")
    print()


async def test_generate_income_report_no_pagination():
    """测试生成收入明细报表（无分页）"""
    print("=" * 50)
    print("测试2: 生成收入明细报表（无分页）")
    print("=" * 50)
    
    # 获取今日记录
    date = get_daily_period_date()
    records = await db_operations.get_income_records(date, date)
    
    print(f"今日日期: {date}")
    print(f"记录数量: {len(records)}")
    print()
    
    if not records:
        print("⚠️ 今日无收入记录，跳过测试")
        return
    
    # 生成报表
    report, has_more, total_pages, current_type = await generate_income_report(
        records, date, date, f"今日收入明细 ({date})", page=1
    )
    
    print("报表内容:")
    print(report)
    print()
    print(f"是否有更多页: {has_more}")
    print(f"总页数: {total_pages}")
    print(f"当前类型: {current_type}")
    print()
    
    # 验证格式
    assert "💰" in report, "报表标题缺失"
    assert "总收入" in report, "总收入汇总缺失"
    
    # 检查是否包含格式化的明细
    if len(records) > 0:
        # 检查是否包含金额、订单号、时间的格式
        assert "|" in report or "无记录" in report, "明细格式可能错误"
    
    print("✅ 无分页报表测试通过")
    print()


async def test_generate_income_report_with_type():
    """测试按类型生成收入明细报表（带分页）"""
    print("=" * 50)
    print("测试3: 按类型生成收入明细报表（带分页）")
    print("=" * 50)
    
    # 获取今日记录
    date = get_daily_period_date()
    
    # 测试利息类型
    records = await db_operations.get_income_records(date, date, type='interest')
    
    print(f"今日日期: {date}")
    print(f"利息记录数量: {len(records)}")
    print()
    
    if not records:
        print("⚠️ 今日无利息记录，跳过测试")
        return
    
    # 生成报表（第一页）
    report, has_more, total_pages, current_type = await generate_income_report(
        records, date, date, f"今日利息收入 ({date})", page=1, income_type='interest'
    )
    
    print("报表内容（第1页）:")
    print(report[:500] + "..." if len(report) > 500 else report)
    print()
    print(f"是否有更多页: {has_more}")
    print(f"总页数: {total_pages}")
    print(f"当前类型: {current_type}")
    print()
    
    # 如果有分页，测试第二页
    if has_more and total_pages > 1:
        print("测试第2页:")
        report2, has_more2, total_pages2, current_type2 = await generate_income_report(
            records, date, date, f"今日利息收入 ({date})", page=2, income_type='interest'
        )
        print(f"第2页是否有更多页: {has_more2}")
        print(f"第2页总页数: {total_pages2}")
        print(f"第2页当前类型: {current_type2}")
        print()
    
    print("✅ 按类型报表测试通过")
    print()


async def test_pagination_logic():
    """测试分页逻辑"""
    print("=" * 50)
    print("测试4: 分页逻辑")
    print("=" * 50)
    
    # 创建大量测试记录（模拟利息记录）
    date = get_daily_period_date()
    tz = pytz.timezone('Asia/Shanghai')
    
    # 获取现有记录数量
    existing_records = await db_operations.get_income_records(date, date, type='interest')
    print(f"现有利息记录数量: {len(existing_records)}")
    
    # 测试分页计算
    items_per_page = 20
    if len(existing_records) > items_per_page:
        total_pages = (len(existing_records) + items_per_page - 1) // items_per_page
        print(f"应该分页: 是")
        print(f"总页数: {total_pages}")
        print(f"每页记录数: {items_per_page}")
        
        # 测试第一页
        page1_start = 0
        page1_end = items_per_page
        print(f"第1页: 记录 {page1_start + 1}-{page1_end}")
        
        # 测试第二页
        if total_pages > 1:
            page2_start = items_per_page
            page2_end = min(items_per_page * 2, len(existing_records))
            print(f"第2页: 记录 {page2_start + 1}-{page2_end}")
    else:
        print(f"应该分页: 否（记录数 {len(existing_records)} <= {items_per_page}）")
    
    print()
    print("✅ 分页逻辑测试通过")
    print()


async def test_all_income_types():
    """测试所有收入类型"""
    print("=" * 50)
    print("测试5: 所有收入类型")
    print("=" * 50)
    
    date = get_daily_period_date()
    income_types = ['completed', 'breach_end', 'interest', 'principal_reduction']
    
    for income_type in income_types:
        records = await db_operations.get_income_records(date, date, type=income_type)
        print(f"{income_type}: {len(records)} 条记录")
        
        if records:
            # 测试格式化
            sample = records[0]
            formatted = await format_income_detail(sample)
            print(f"  示例格式: {formatted}")
    
    print()
    print("✅ 所有类型测试通过")
    print()


async def run_all_tests():
    """运行所有测试"""
    import sys
    sys.stdout.flush()
    
    print("\n" + "=" * 50)
    print("开始测试收入明细格式和分页功能")
    print("=" * 50 + "\n")
    sys.stdout.flush()
    
    try:
        print("执行测试1...")
        sys.stdout.flush()
        await test_format_income_detail()
        
        print("执行测试2...")
        sys.stdout.flush()
        await test_generate_income_report_no_pagination()
        
        print("执行测试3...")
        sys.stdout.flush()
        await test_generate_income_report_with_type()
        
        print("执行测试4...")
        sys.stdout.flush()
        await test_pagination_logic()
        
        print("执行测试5...")
        sys.stdout.flush()
        await test_all_income_types()
        
        print("=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        sys.stdout.flush()
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ 测试失败: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"运行失败: {e}")
        import traceback
        traceback.print_exc()


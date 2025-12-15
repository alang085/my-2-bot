"""测试增量报表系统"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入模块
import init_db
import db_operations
from utils.incremental_report_generator import get_or_create_baseline_date, prepare_incremental_data
from utils.incremental_report_merger import calculate_incremental_stats, preview_incremental_report
from utils.excel_export import export_incremental_orders_report_to_excel
from datetime import datetime, timedelta
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


async def test_baseline_date():
    """测试基准日期管理"""
    print("=" * 60)
    print("测试1: 基准日期管理")
    print("=" * 60)
    
    # 测试获取或创建基准日期
    baseline_date = await get_or_create_baseline_date()
    print(f"✅ 基准日期: {baseline_date}")
    
    # 测试检查基准日期是否存在
    exists = await db_operations.check_baseline_exists()
    print(f"✅ 基准日期存在: {exists}")
    
    # 测试获取基准日期
    retrieved_date = await db_operations.get_baseline_date()
    print(f"✅ 获取的基准日期: {retrieved_date}")
    
    print()


async def test_incremental_data():
    """测试增量数据准备"""
    print("=" * 60)
    print("测试2: 增量数据准备")
    print("=" * 60)
    
    baseline_date = await get_or_create_baseline_date()
    print(f"基准日期: {baseline_date}")
    
    # 准备增量数据
    incremental_data = await prepare_incremental_data(baseline_date)
    
    orders_data = incremental_data.get('orders', [])
    expense_records = incremental_data.get('expenses', [])
    
    print(f"✅ 增量订单数: {len(orders_data)}")
    print(f"✅ 增量开销记录数: {len(expense_records)}")
    
    if orders_data:
        print(f"\n前3个订单示例:")
        for i, order in enumerate(orders_data[:3], 1):
            order_id = order.get('order_id', '未知')
            amount = order.get('amount', 0)
            total_interest = order.get('total_interest', 0)
            interests = order.get('interests', [])
            print(f"  {i}. {order_id} - 金额: {amount:,.2f}, 利息: {total_interest:,.2f}, 利息笔数: {len(interests)}")
    
    print()


async def test_incremental_stats():
    """测试增量统计计算"""
    print("=" * 60)
    print("测试3: 增量统计计算")
    print("=" * 60)
    
    baseline_date = await get_or_create_baseline_date()
    incremental_data = await prepare_incremental_data(baseline_date)
    
    orders_data = incremental_data.get('orders', [])
    expense_records = incremental_data.get('expenses', [])
    
    stats = await calculate_incremental_stats(orders_data, expense_records)
    
    print(f"📦 订单统计:")
    print(f"  - 新增订单数: {stats['new_orders_count']}")
    print(f"  - 新增订单金额: {stats['new_orders_amount']:,.2f}")
    print(f"  - 新客户数: {stats['new_clients_count']}")
    print(f"  - 新客户金额: {stats['new_clients_amount']:,.2f}")
    print(f"  - 老客户数: {stats['old_clients_count']}")
    print(f"  - 老客户金额: {stats['old_clients_amount']:,.2f}")
    
    print(f"\n💰 收入统计:")
    print(f"  - 利息: {stats['interest']:,.2f}")
    print(f"  - 归还本金: {stats['principal_reduction']:,.2f}")
    print(f"  - 完成订单数: {stats['completed_orders_count']}")
    print(f"  - 完成订单金额: {stats['completed_amount']:,.2f}")
    
    print(f"\n💸 开销统计:")
    print(f"  - 公司开销: {stats['company_expenses']:,.2f}")
    print(f"  - 其他开销: {stats['other_expenses']:,.2f}")
    print(f"  - 总开销: {stats['company_expenses'] + stats['other_expenses']:,.2f}")
    
    print()


async def test_preview():
    """测试预览功能"""
    print("=" * 60)
    print("测试4: 增量报表预览")
    print("=" * 60)
    
    baseline_date = await get_or_create_baseline_date()
    preview_text = await preview_incremental_report(baseline_date)
    print(preview_text)
    print()


async def test_excel_export():
    """测试Excel导出"""
    print("=" * 60)
    print("测试5: Excel报表导出")
    print("=" * 60)
    
    baseline_date = await get_or_create_baseline_date()
    current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    
    incremental_data = await prepare_incremental_data(baseline_date)
    orders_data = incremental_data.get('orders', [])
    expense_records = incremental_data.get('expenses', [])
    
    try:
        excel_path = await export_incremental_orders_report_to_excel(
            baseline_date,
            current_date,
            orders_data,
            expense_records
        )
        print(f"✅ Excel报表已生成: {excel_path}")
        print(f"✅ 文件大小: {os.path.getsize(excel_path) / 1024:.2f} KB")
        
        if os.path.exists(excel_path):
            print(f"✅ 文件存在，可以打开查看")
        else:
            print(f"❌ 文件不存在")
    except Exception as e:
        print(f"❌ Excel导出失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()


async def test_merge_records():
    """测试合并记录管理"""
    print("=" * 60)
    print("测试6: 合并记录管理")
    print("=" * 60)
    
    current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    
    # 检查合并记录
    merge_record = await db_operations.get_merge_record(current_date)
    if merge_record:
        print(f"✅ 找到合并记录:")
        print(f"  - 合并日期: {merge_record.get('merge_date')}")
        print(f"  - 订单数: {merge_record.get('orders_count')}")
        print(f"  - 订单金额: {merge_record.get('total_amount', 0):,.2f}")
        print(f"  - 利息: {merge_record.get('total_interest', 0):,.2f}")
        print(f"  - 开销: {merge_record.get('total_expenses', 0):,.2f}")
        print(f"  - 合并时间: {merge_record.get('merged_at')}")
    else:
        print(f"ℹ️  {current_date} 尚未合并过")
    
    # 获取所有合并记录
    all_records = await db_operations.get_all_merge_records()
    print(f"\n✅ 总合并记录数: {len(all_records)}")
    if all_records:
        print(f"最近3条合并记录:")
        for i, record in enumerate(all_records[:3], 1):
            print(f"  {i}. {record.get('merge_date')} - {record.get('orders_count')}个订单, {record.get('total_amount', 0):,.2f}")
    
    print()


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("增量报表系统测试")
    print("=" * 60 + "\n")
    
    try:
        # 初始化数据库（如果表不存在）
        print("初始化数据库...")
        init_db.init_database()
        print("✅ 数据库初始化完成\n")
        
        # 运行测试
        await test_baseline_date()
        await test_incremental_data()
        await test_incremental_stats()
        await test_preview()
        await test_excel_export()
        await test_merge_records()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

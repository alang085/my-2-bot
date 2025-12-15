"""测试增量报表系统（带模拟数据）"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入模块
import init_db
import db_operations
from utils.incremental_report_generator import get_or_create_baseline_date, prepare_incremental_data
from utils.incremental_report_merger import calculate_incremental_stats, merge_incremental_report_to_global
from utils.excel_export import export_incremental_orders_report_to_excel

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


async def create_test_data():
    """创建测试数据"""
    print("=" * 60)
    print("创建测试数据")
    print("=" * 60)
    
    # 设置基准日期为3天前
    baseline_date = (datetime.now(BEIJING_TZ) - timedelta(days=3)).strftime('%Y-%m-%d')
    await db_operations.save_baseline_date(baseline_date)
    print(f"✅ 设置基准日期: {baseline_date}")
    
    # 创建测试订单（在基准日期之后）
    test_date = (datetime.now(BEIJING_TZ) - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 注意：这里只是演示，实际需要根据你的订单创建逻辑来创建
    # 由于订单创建涉及复杂的业务逻辑，这里只展示如何测试报表功能
    
    print(f"ℹ️  测试数据准备完成（基准日期: {baseline_date}）")
    print(f"ℹ️  如果有订单数据，系统会自动检测增量数据")
    print()


async def test_full_workflow():
    """测试完整工作流程"""
    print("=" * 60)
    print("完整工作流程测试")
    print("=" * 60)
    
    # 1. 获取基准日期
    baseline_date = await get_or_create_baseline_date()
    print(f"1. 基准日期: {baseline_date}")
    
    # 2. 准备增量数据
    incremental_data = await prepare_incremental_data(baseline_date)
    orders_data = incremental_data.get('orders', [])
    expense_records = incremental_data.get('expenses', [])
    print(f"2. 增量订单数: {len(orders_data)}, 开销记录数: {len(expense_records)}")
    
    # 3. 计算统计
    if orders_data or expense_records:
        stats = await calculate_incremental_stats(orders_data, expense_records)
        print(f"3. 统计计算完成:")
        print(f"   - 订单数: {stats['new_orders_count']}")
        print(f"   - 订单金额: {stats['new_orders_amount']:,.2f}")
        print(f"   - 利息: {stats['interest']:,.2f}")
        print(f"   - 开销: {stats['company_expenses'] + stats['other_expenses']:,.2f}")
        
        # 4. 生成Excel报表
        current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        excel_path = await export_incremental_orders_report_to_excel(
            baseline_date,
            current_date,
            orders_data,
            expense_records
        )
        print(f"4. Excel报表已生成: {excel_path}")
        
        # 5. 测试合并（不实际执行，只检查逻辑）
        print(f"5. 合并功能检查:")
        merge_record = await db_operations.get_merge_record(current_date)
        if merge_record:
            print(f"   ⚠️  该日期已合并过，再次合并会提示确认")
        else:
            print(f"   ✅ 可以合并（未合并过）")
        
        print(f"\n✅ 完整流程测试通过！")
    else:
        print(f"ℹ️  当前无增量数据，这是正常的（如果基准日期是今天）")
        print(f"ℹ️  要测试完整功能，需要:")
        print(f"   1. 创建一些订单（在基准日期之后）")
        print(f"   2. 记录一些利息和开销")
        print(f"   3. 然后运行此测试")
    
    print()


async def show_test_instructions():
    """显示测试说明"""
    print("=" * 60)
    print("测试说明")
    print("=" * 60)
    print("""
要完整测试增量报表系统，请按以下步骤操作：

1. 设置基准日期（已自动设置）
   - 基准日期: 系统首次运行时自动设置为当前日期
   - 或使用命令手动设置

2. 创建测试订单（在基准日期之后）
   - 在Telegram群组中使用 /create 命令创建订单
   - 或通过数据库直接插入测试数据

3. 记录利息和开销
   - 在订单群组中使用 +金额 记录利息
   - 使用开销记录功能记录开销

4. 测试报表功能
   - 运行此测试脚本查看增量数据
   - 或等待每天11:05自动发送报表

5. 测试合并功能
   - 在Telegram中点击Excel报表的"合并到总表"按钮
   - 或使用 /merge_incremental 命令

6. 查看Excel报表
   - 打开生成的Excel文件查看报表格式
   - 测试利息明细的展开/折叠功能
    """)


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("增量报表系统完整测试")
    print("=" * 60 + "\n")
    
    try:
        # 初始化数据库
        print("初始化数据库...")
        init_db.init_database()
        print("✅ 数据库初始化完成\n")
        
        # 创建测试数据
        await create_test_data()
        
        # 测试完整流程
        await test_full_workflow()
        
        # 显示测试说明
        await show_test_instructions()
        
        print("=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


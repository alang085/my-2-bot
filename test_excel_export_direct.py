"""直接测试Excel导出功能（不依赖数据库数据）"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import pytz

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.excel_export import create_incremental_orders_report_file

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


def test_excel_with_mock_data():
    """使用模拟数据测试Excel导出"""
    print("=" * 60)
    print("测试Excel导出功能（使用模拟数据）")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = os.path.join(project_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 模拟数据
    baseline_date = "2025-12-15"
    current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    
    # 模拟订单数据
    orders_data = [
        {
            'order_id': 'ORD001',
            'date': '2025-12-16',
            'created_at': '2025-12-16 10:00:00',
            'customer': 'A',
            'amount': 10000.0,
            'state': 'normal',
            'total_interest': 1500.0,
            'principal_reduction': 2000.0,
            'interests': [
                {'date': '2025-12-16', 'amount': 500.0},
                {'date': '2025-12-17', 'amount': 500.0},
                {'date': '2025-12-18', 'amount': 500.0}
            ],
            'note': '新订单'
        },
        {
            'order_id': 'ORD002',
            'date': '2025-12-16',
            'created_at': '2025-12-16 11:00:00',
            'customer': 'B',
            'amount': 20000.0,
            'state': 'normal',
            'total_interest': 1000.0,
            'principal_reduction': 0.0,
            'interests': [
                {'date': '2025-12-16', 'amount': 1000.0}
            ],
            'note': '新订单'
        },
        {
            'order_id': 'ORD003',
            'date': '2025-12-16',
            'created_at': '2025-12-16 12:00:00',
            'customer': 'A',
            'amount': 15000.0,
            'state': 'end',
            'total_interest': 750.0,
            'principal_reduction': 15000.0,
            'interests': [
                {'date': '2025-12-16', 'amount': 750.0}
            ],
            'note': '订单完成'
        }
    ]
    
    # 模拟开销数据
    expense_records = [
        {
            'date': '2025-12-16',
            'type': 'company',
            'amount': 500.0,
            'note': '办公用品'
        },
        {
            'date': '2025-12-16',
            'type': 'other',
            'amount': 200.0,
            'note': '其他费用'
        }
    ]
    
    # 生成Excel文件
    file_name = f"测试增量报表_{current_date}.xlsx"
    file_path = os.path.join(temp_dir, file_name)
    
    try:
        print(f"生成Excel文件: {file_path}")
        result_path = create_incremental_orders_report_file(
            file_path,
            baseline_date,
            current_date,
            orders_data,
            expense_records
        )
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✅ Excel文件已生成: {result_path}")
            print(f"✅ 文件大小: {file_size:,} 字节")
            print(f"\n📊 报表内容:")
            print(f"  - 订单数: {len(orders_data)}")
            print(f"  - 开销记录数: {len(expense_records)}")
            print(f"  - 基准日期: {baseline_date}")
            print(f"  - 当前日期: {current_date}")
            print(f"\n💡 提示:")
            print(f"  1. 打开Excel文件查看报表")
            print(f"  2. 检查利息总数列是否可以展开查看明细")
            print(f"  3. 检查汇总行是否正确")
            print(f"  4. 检查开销明细表是否存在")
        else:
            print(f"❌ Excel文件不存在: {result_path}")
    except Exception as e:
        print(f"❌ Excel导出失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_excel_with_mock_data()


"""测试每日数据变更表功能"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import pytz

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入模块
import init_db
from handlers.daily_changes_handlers import get_daily_changes, generate_changes_table

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


async def test_daily_changes():
    """测试每日数据变更表"""
    print("=" * 60)
    print("测试每日数据变更表")
    print("=" * 60)
    
    # 初始化数据库
    print("初始化数据库...")
    init_db.init_database()
    print("✅ 数据库初始化完成\n")
    
    # 测试当前日期的数据变更
    current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    print(f"查询日期: {current_date}\n")
    
    # 获取每日数据变更
    changes = await get_daily_changes(current_date)
    
    # 生成表格文本
    table_text = generate_changes_table(current_date, changes)
    
    # 显示结果（去掉HTML标签以便在控制台显示）
    display_text = table_text.replace('<b>', '').replace('</b>', '')
    print(display_text)
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    print("\n💡 提示：在Telegram中使用以下命令查看：")
    print(f"   /daily_changes {current_date}")
    print("   或")
    print("   /daily_changes  （查看今天的变更）")


if __name__ == "__main__":
    asyncio.run(test_daily_changes())


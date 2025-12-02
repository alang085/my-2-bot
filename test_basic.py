"""基本功能测试脚本 - 验证核心模块是否可以正常导入和初始化"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有核心模块是否可以正常导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)
    
    try:
        print("✓ 导入 config...")
        from config import BOT_TOKEN, ADMIN_IDS
        print(f"  BOT_TOKEN: {'已设置' if BOT_TOKEN else '未设置'}")
        print(f"  ADMIN_IDS: {len(ADMIN_IDS) if ADMIN_IDS else 0} 个管理员")
    except Exception as e:
        print(f"✗ 导入 config 失败: {e}")
        return False
    
    try:
        print("✓ 导入 db_operations...")
        import db_operations
        print("  db_operations 模块导入成功")
    except Exception as e:
        print(f"✗ 导入 db_operations 失败: {e}")
        return False
    
    try:
        print("✓ 导入 handlers...")
        from handlers import start, create_order, show_report
        print("  handlers 模块导入成功")
    except Exception as e:
        print(f"✗ 导入 handlers 失败: {e}")
        return False
    
    try:
        print("✓ 导入 callbacks...")
        from callbacks import button_callback
        print("  callbacks 模块导入成功")
    except Exception as e:
        print(f"✗ 导入 callbacks 失败: {e}")
        return False
    
    try:
        print("✓ 导入 utils...")
        from utils import is_group_chat, get_daily_period_date
        print("  utils 模块导入成功")
    except Exception as e:
        print(f"✗ 导入 utils 失败: {e}")
        return False
    
    try:
        print("✓ 导入 decorators...")
        from decorators import error_handler, admin_required
        print("  decorators 模块导入成功")
    except Exception as e:
        print(f"✗ 导入 decorators 失败: {e}")
        return False
    
    return True


def test_database():
    """测试数据库连接和基本操作"""
    print("\n" + "=" * 60)
    print("测试数据库连接...")
    print("=" * 60)
    
    try:
        import db_operations
        import asyncio
        
        async def test_db():
            # 测试获取财务数据
            print("✓ 测试获取财务数据...")
            financial_data = await db_operations.get_financial_data()
            print(f"  有效订单数: {financial_data.get('valid_orders', 0)}")
            print(f"  有效订单金额: {financial_data.get('valid_amount', 0):.2f}")
            
            # 测试获取授权用户
            print("✓ 测试获取授权用户...")
            authorized_users = await db_operations.get_authorized_users()
            print(f"  授权用户数: {len(authorized_users)}")
            
            return True
        
        result = asyncio.run(test_db())
        return result
        
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_init_db():
    """测试数据库初始化"""
    print("\n" + "=" * 60)
    print("测试数据库初始化...")
    print("=" * 60)
    
    try:
        import init_db
        print("✓ 初始化数据库...")
        init_db.init_database()
        print("  数据库初始化成功")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始基本功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试模块导入
    results.append(("模块导入", test_imports()))
    
    # 测试数据库初始化
    results.append(("数据库初始化", test_init_db()))
    
    # 测试数据库连接
    results.append(("数据库连接", test_database()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit(main())


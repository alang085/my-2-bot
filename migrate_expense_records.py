"""数据库迁移脚本：创建 expense_records 表"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(DATA_DIR, 'loan_bot.db')


def migrate_expense_records():
    """创建 expense_records 表（如果不存在）"""
    if not os.path.exists(DB_NAME):
        logger.warning(f"数据库文件不存在: {DB_NAME}")
        print(f"数据库文件不存在: {DB_NAME}")
        return False

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 检查表是否已存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='expense_records'")
        table_exists = cursor.fetchone()

        if table_exists:
            print("expense_records 表已存在，无需创建")
            logger.info("expense_records 表已存在，无需创建")
            conn.close()
            return True

        # 创建表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

        print("✅ expense_records 表创建成功！")
        logger.info("expense_records 表创建成功")
        return True

    except Exception as e:
        logger.error(f"创建 expense_records 表失败: {e}", exc_info=True)
        print(f"❌ 创建 expense_records 表失败: {e}")
        return False


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    migrate_expense_records()


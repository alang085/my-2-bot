"""为 operation_history 表添加 chat_id 字段的迁移脚本"""
import sqlite3
import os

DB_PATH = 'loan_bot.db'

def migrate():
    """执行迁移"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件 {DB_PATH} 不存在，跳过迁移")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查 chat_id 字段是否已存在
        cursor.execute("PRAGMA table_info(operation_history)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'chat_id' in columns:
            print("✅ chat_id 字段已存在，跳过迁移")
            return
        
        print("开始迁移：为 operation_history 表添加 chat_id 字段...")
        
        # 添加 chat_id 字段（使用默认值 0，表示历史数据）
        cursor.execute('''
        ALTER TABLE operation_history 
        ADD COLUMN chat_id INTEGER NOT NULL DEFAULT 0
        ''')
        
        # 创建新索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_operation_chat_user 
        ON operation_history(chat_id, user_id, created_at DESC)
        ''')
        
        conn.commit()
        print("✅ 迁移完成：已添加 chat_id 字段和索引")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()


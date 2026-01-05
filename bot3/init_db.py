import logging
import os
import sqlite3

from db.init_tables_customer import create_customer_tables
from db.init_tables_finance import create_finance_tables
from db.init_tables_messages import create_message_tables
from db.init_tables_orders import (create_classified_tables,
                                   create_orders_tables)
from db.init_tables_payment import create_payment_tables
from db.init_tables_records import create_record_tables
from db.init_tables_reports import create_report_tables
from db.init_tables_users import create_user_tables

logger = logging.getLogger(__name__)

# 数据库文件路径 - 支持持久化存储
# 如果设置了 DATA_DIR 环境变量，使用该目录；否则使用当前目录
DATA_DIR = os.getenv("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "loan_bot.db")


def init_database():
    """初始化数据库，创建所有必要的表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 创建订单相关表
    create_orders_tables(cursor)
    create_classified_tables(cursor)

    # 创建财务数据表
    create_finance_tables(cursor, conn)

    # 创建用户和权限表
    create_user_tables(cursor)

    # 创建支付相关表
    create_payment_tables(cursor, conn)

    # 创建消息和自动化表
    create_message_tables(cursor)

    # 创建财务记录表
    create_record_tables(cursor)

    # 创建报表相关表
    create_report_tables(cursor, conn)

    # 创建客户信用系统表
    create_customer_tables(cursor)

    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")


if __name__ == "__main__":
    init_database()

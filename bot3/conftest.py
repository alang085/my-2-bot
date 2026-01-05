"""Pytest配置和fixtures"""

import asyncio
import os
import tempfile

import pytest

# 导入测试配置（在导入其他模块之前设置环境变量）
from tests.test_config import setup_test_config

# 设置测试配置
setup_test_config()

# 设置测试数据库路径
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "test_loan_bot.db")

# 导入扩展fixtures
from tests.fixtures.database import db_connection  # noqa: E402, F401
from tests.fixtures.database import (sample_financial_data, sample_order_data,
                                     temp_db)
from tests.fixtures.mock_data import mock_admin_user  # noqa: E402, F401
from tests.fixtures.mock_data import (mock_authorized_user,
                                      mock_financial_data, mock_order_list,
                                      mock_unauthorized_user)
from tests.fixtures.telegram import mock_application  # noqa: E402, F401
from tests.fixtures.telegram import (mock_bot, telegram_callback_update,
                                     telegram_context, telegram_update)


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    # 删除旧的测试数据库
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # 初始化测试数据库
    from init_db import init_database

    # 临时设置数据库路径
    original_db_name = None
    try:
        import init_db

        original_db_name = init_db.DB_NAME
        init_db.DB_NAME = TEST_DB_PATH
        init_database()
        yield TEST_DB_PATH
    finally:
        # 恢复原始数据库路径
        if original_db_name:
            init_db.DB_NAME = original_db_name
        # 清理测试数据库
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_update():
    """创建模拟的Update对象"""
    from tests.test_config import mock_telegram_update

    return mock_telegram_update(user_id=67890, chat_id=12345, text="/test")


@pytest.fixture
def mock_context():
    """创建模拟的Context对象"""
    from tests.test_config import mock_telegram_context

    return mock_telegram_context(args=[], user_data={})


@pytest.fixture(autouse=True)
def setup_test_env():
    """自动设置测试环境（每个测试前自动运行）"""
    setup_test_config()
    yield
    # 测试后清理（如果需要）

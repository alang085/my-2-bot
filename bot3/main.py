"""Telegram订单管理机器人主入口 - bot3 重组版本"""

# 标准库导入
import logging
import os
import sys
from pathlib import Path

# 第三方库导入
from telegram import error as telegram_error
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          MessageHandler, filters)

# 本地模块导入
import init_db
from config import ADMIN_IDS, BOT_TOKEN
# 基础命令
from handlers.command_handlers_basic import (check_permission,
                                             show_valid_amount, start)
from handlers.module1_user.attribution_handlers import (
    change_orders_attribution, create_attribution, list_attributions)
# 模块1：用户权限管理
from handlers.module1_user.employee_handlers import (add_employee,
                                                     list_employees,
                                                     remove_employee)
from handlers.module1_user.user_mapping_handlers import (
    list_user_group_mappings, remove_user_group_id_handler,
    set_user_group_id_handler)
# 模块2：财务管理
from handlers.module2_finance.adjustment_handlers import adjust_funds
from handlers.module2_finance.income_handlers import *  # noqa: F401, F403
from handlers.module2_finance.payment_handlers import (balance_history,
                                                       show_all_accounts,
                                                       show_gcash,
                                                       show_paymaya)
# 模块3：订单管理
from handlers.module3_order.amount_handlers import handle_amount_operation
from handlers.module3_order.basic_handlers import (create_order,
                                                   show_current_order)
from handlers.module3_order.state_handlers import (set_breach, set_breach_end,
                                                   set_end, set_normal,
                                                   set_overdue)
# 模块4：自动化任务
from handlers.module4_automation.broadcast_handlers import broadcast_payment
from handlers.module4_automation.chat_event_handlers import (
    handle_new_chat_members, handle_new_chat_title)
from handlers.module4_automation.group_message_handlers import (
    get_group_id, list_group_message_configs, send_start_work_messages_command,
    setup_group_auto, test_group_message, test_weekday_message)
from handlers.module4_automation.schedule_handlers import show_schedule_menu
from handlers.module4_automation.search_handlers import search_orders
from handlers.module4_automation.text_input_handlers import handle_text_input
# 模块5：数据管理
from handlers.module5_data.admin_correction_handlers import admin_correct
from handlers.module5_data.daily_changes_handlers import \
    show_daily_changes_table
from handlers.module5_data.daily_operations_handlers import (
    show_daily_operations, show_daily_operations_summary)
from handlers.module5_data.diagnostic_handlers import (
    check_mismatch, diagnose_data_inconsistency)
from handlers.module5_data.import_handlers import (import_orders_command,
                                                   import_orders_from_excel)
from handlers.module5_data.order_table_handlers import show_order_table
from handlers.module5_data.report_handlers import show_my_report, show_report
from handlers.module5_data.restore_handlers import restore_daily_data
from handlers.module5_data.stats_handlers import (fix_income_statistics,
                                                  fix_statistics)
from handlers.module5_data.tools_handlers import (customer_contribution,
                                                  find_tail_orders)
from handlers.module5_data.undo_handlers import undo_last_operation
from handlers.module5_data.weekday_handlers import (check_weekday_groups,
                                                    update_weekday_groups)
from main_handlers_automation import register_automation_handlers
from main_handlers_basic import register_basic_handlers
from main_handlers_callbacks import register_callback_handlers
from main_handlers_data import register_data_handlers
from main_handlers_finance import register_finance_handlers
from main_handlers_order import register_order_handlers
from main_handlers_user import register_user_handlers

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
project_root_str = str(project_root)

if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO if os.getenv("DEBUG", "0") != "1" else logging.DEBUG,
)
logger = logging.getLogger(__name__)

# 降低日志级别
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)


def main() -> None:
    """启动机器人"""
    # 验证配置
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN 未设置，无法启动机器人")
        return

    if not ADMIN_IDS:
        logger.error("ADMIN_USER_IDS 未设置，无法启动机器人")
        return

    logger.info(f"机器人启动中... 管理员数量: {len(ADMIN_IDS)}")

    # 初始化数据库
    logger.info("检查数据库...")
    try:
        init_db.init_database()
        logger.info("数据库已就绪")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        return

    # 创建Application
    try:
        from telegram.request import HTTPXRequest

        request = HTTPXRequest(
            connection_pool_size=20,
            read_timeout=60,
            write_timeout=60,
            connect_timeout=30,
            pool_timeout=30,
        )

        application = Application.builder().token(BOT_TOKEN).request(request).build()
        logger.info("应用创建成功")
    except Exception as e:
        logger.error(f"创建应用时出错: {e}", exc_info=True)
        return

    # 注册所有处理器
    register_basic_handlers(application)
    register_order_handlers(application)
    register_user_handlers(application)
    register_finance_handlers(application)
    register_automation_handlers(application)
    register_data_handlers(application)
    register_callback_handlers(application)

    # 启动机器人
    logger.info("机器人启动成功，等待消息...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES, drop_pending_updates=True
        )
    except telegram_error.NetworkError as e:
        logger.error(f"网络错误: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"运行时错误: {e}", exc_info=True)


if __name__ == "__main__":
    main()

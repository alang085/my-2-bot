"""报表相关回调处理器 - 主路由"""

import logging
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from callbacks.report_callbacks_attribution import (
    handle_broadcast_start, handle_change_attribution,
    handle_change_to_attribution, handle_menu_attribution,
    handle_search_orders)
from callbacks.report_callbacks_base import (MockUpdate,
                                             check_expense_permission,
                                             check_user_permission)
from callbacks.report_callbacks_expense import (handle_expense_company_add,
                                                handle_expense_company_month,
                                                handle_expense_company_query,
                                                handle_expense_company_today,
                                                handle_expense_other_add,
                                                handle_expense_other_month,
                                                handle_expense_other_query,
                                                handle_expense_other_today)
from callbacks.report_callbacks_income import (handle_income_adv_page,
                                               handle_income_advanced_query,
                                               handle_income_page,
                                               handle_income_query_group,
                                               handle_income_query_step_date,
                                               handle_income_query_step_type,
                                               handle_income_query_type,
                                               handle_income_type,
                                               handle_income_view_by_type,
                                               handle_income_view_month,
                                               handle_income_view_query,
                                               handle_income_view_today)
from callbacks.report_callbacks_order_table import (
    handle_order_table_export_excel, handle_order_table_view)
from callbacks.report_callbacks_view import (handle_report_view_month,
                                             handle_report_view_query,
                                             handle_report_view_today)
from handlers.data_access import get_user_group_id

logger = logging.getLogger(__name__)


async def handle_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理报表相关的回调"""
    from callbacks.report_attribution_handlers import \
        handle_attribution_callbacks
    from callbacks.report_expense_handlers import handle_expense_callbacks
    from callbacks.report_income_handlers import handle_income_callbacks
    from callbacks.report_order_table_handlers import \
        handle_order_table_callbacks
    from callbacks.report_validate import validate_report_callback
    from callbacks.report_view_handlers import handle_report_view_callbacks

    query = update.callback_query
    if not query:
        logger.error("handle_report_callback: query is None")
        return

    # 验证请求
    is_valid, user_id, user_group_id = await validate_report_callback(update, query)
    if not is_valid:
        return

    data = query.data

    # 处理各类回调
    # 1. 开销相关回调
    if await handle_expense_callbacks(data, query, user_id, context):
        return

    # 2. 归属管理相关回调
    if await handle_attribution_callbacks(data, query, update, context):
        return

    # 3. 收入明细查询回调
    if await handle_income_callbacks(data, query, user_id, context):
        return

    # 4. 报表视图回调
    if await handle_report_view_callbacks(data, query, context, user_id, user_group_id):
        return

    # 5. 订单总表回调
    if await handle_order_table_callbacks(data, query, context, user_id):
        return

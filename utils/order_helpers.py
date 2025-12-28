"""订单相关工具函数"""

import logging
import re
from datetime import date, datetime
from typing import Any, Dict, Optional, Tuple, Union

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from constants import HISTORICAL_THRESHOLD_DATE
from utils.chat_helpers import (
    get_weekday_group_from_date,
    is_group_chat,
    reply_in_group,
)
from utils.message_builders import build_order_creation_message
from utils.models import OrderCreateModel, validate_amount
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


def _parse_current_order_date(date_str: str) -> Optional[date]:
    """解析当前订单日期字符串

    Args:
        date_str: 日期字符串，格式可能是 "YYYY-MM-DD HH:MM:SS" 或 "YYYY-MM-DD"

    Returns:
        解析后的日期对象，如果解析失败返回 None
    """
    if not date_str:
        return None

    try:
        # 提取日期部分（去掉时间部分）
        date_part = date_str.split()[0] if " " in date_str else date_str
        return datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        try:
            # 尝试其他日期格式
            return datetime.strptime(date_part, "%Y/%m/%d").date()
        except ValueError:
            logger.debug(f"无法解析订单日期: {date_str}")
            return None


async def _update_order_date_and_weekday(
    order: Dict[str, Any],
    chat_id: int,
    new_order_date: date,
    order_id: str,
) -> bool:
    """更新订单日期和星期分组

    Args:
        order: 订单字典
        chat_id: 聊天ID
        new_order_date: 新的订单日期
        order_id: 订单ID（用于日志）

    Returns:
        是否成功更新
    """
    try:
        # 计算新的星期分组（基于群名中的日期）
        new_weekday_group = get_weekday_group_from_date(new_order_date)
        current_weekday_group = order.get("weekday_group", "")

        logger.info(
            f"订单 {order_id} 群名更新: 新日期={new_order_date}, "
            f"当前星期分组={current_weekday_group}, 新星期分组={new_weekday_group}"
        )

        # 构造新的日期字符串（保持原有格式：YYYY-MM-DD HH:MM:SS）
        new_date_str = f"{new_order_date.strftime('%Y-%m-%d')} 12:00:00"

        # 更新订单日期
        date_update_success = await db_operations.update_order_date(chat_id, new_date_str)
        if not date_update_success:
            logger.warning(f"更新订单日期失败: chat_id={chat_id}, new_date={new_date_str}")
            return False

        # 更新星期分组（基于群名中的日期）
        if current_weekday_group != new_weekday_group:
            logger.info(
                f"订单 {order_id} 星期分组需要更新: {current_weekday_group} -> {new_weekday_group}"
            )
            weekday_update_success = await db_operations.update_order_weekday_group(
                chat_id, new_weekday_group
            )
            if not weekday_update_success:
                logger.warning(
                    f"更新订单星期分组失败: chat_id={chat_id}, new_weekday_group={new_weekday_group}"
                )
                return False
        else:
            logger.debug(f"订单 {order_id} 星期分组已正确 ({current_weekday_group})，无需更新")

        # 更新 order 字典中的日期和星期分组，以便后续使用
        order["date"] = new_date_str
        order["weekday_group"] = new_weekday_group
        logger.info(f"订单 {order_id} 日期和星期分组已更新: {new_order_date}, {new_weekday_group}")
        return True

    except Exception as e:
        logger.error(f"更新订单日期和星期分组时出错: {e}", exc_info=True)
        return False


def _validate_state_transition(current_state: str, target_state: str, order_id: str) -> bool:
    """验证状态转换是否合法

    Args:
        current_state: 当前状态
        target_state: 目标状态
        order_id: 订单ID（用于日志）

    Returns:
        是否允许转换
    """
    # 归档状态（end、breach_end）完全不可更改，但此函数只会在非归档状态时被调用
    # 这里额外检查以防万一
    if current_state in ["end", "breach_end"]:
        logger.info(f"订单 {order_id} 当前状态为 {current_state}（归档状态），禁止任何状态变更")
        return False

    is_current_valid = current_state in ["normal", "overdue"]
    is_target_valid = target_state in ["normal", "overdue"]
    is_current_breach = current_state == "breach"
    is_target_end = target_state == "end"
    is_target_breach_end = target_state == "breach_end"

    # 禁止违约状态反向变更为正常/逾期
    if is_current_breach and is_target_valid:
        logger.info(f"订单 {order_id} 当前状态为违约，禁止反向变更为 {target_state}")
        return False

    # 检查完成状态的转换规则
    if is_target_end:
        # 只能从 normal 或 overdue 转换到 end
        if not is_current_valid:
            logger.info(
                f"订单 {order_id} 当前状态为 {current_state}，不能直接变更为 end（只能从 normal/overdue 转换）"
            )
            return False

    if is_target_breach_end:
        # 禁止通过群名自动将 breach 变更为 breach_end（只能通过命令手动完成）
        logger.info(f"订单 {order_id} 禁止通过群名自动变更为 breach_end（只能通过命令手动完成）")
        return False

    return True


async def _handle_state_transition_stats(
    update: Update,
    current_state: str,
    target_state: str,
    order: Dict[str, Any],
    group_id: str,
    amount: float,
) -> bool:
    """处理状态转换时的统计数据迁移

    Args:
        update: Telegram 更新对象
        current_state: 当前状态
        target_state: 目标状态
        order: 订单字典
        group_id: 归属ID
        amount: 订单金额

    Returns:
        是否成功处理
    """
    is_current_valid = current_state in ["normal", "overdue"]
    is_target_breach = target_state == "breach"
    is_target_end = target_state == "end"

    if is_current_valid and is_target_breach:
        # Valid -> Breach
        await update_all_stats("valid", -amount, -1, group_id)
        await update_all_stats("breach", amount, 1, group_id)
        await reply_in_group(
            update, f"🔄 State Changed: {target_state} (Auto)\nStats moved to Breach."
        )
        return True

    elif is_current_valid and is_target_end:
        # Valid -> End (完成订单)
        from utils.date_helpers import get_daily_period_date

        user_id = update.effective_user.id if update.effective_user else 0
        date = get_daily_period_date()

        try:
            # 1. 先记录收入明细（如果失败，不更新统计数据）
            await db_operations.record_income(
                date=date,
                type="completed",
                amount=amount,
                group_id=group_id,
                order_id=order.get("order_id", "unknown"),
                order_date=order["date"],
                customer=order["customer"],
                weekday_group=order["weekday_group"],
                note="订单完成（自动）",
                created_by=user_id,
            )
        except Exception as e:
            logger.error(f"记录订单完成收入明细失败（自动完成）: {e}", exc_info=True)
            await reply_in_group(
                update,
                f"❌ Failed to record income details. Order state updated but income not recorded. Error: {str(e)}",
            )
            return False

        # 2. 收入明细记录成功后，再更新统计数据
        try:
            await update_all_stats("valid", -amount, -1, group_id)
            await update_all_stats("completed", amount, 1, group_id)
            # 完成订单需要增加流动资金
            await update_liquid_capital(amount)
            await reply_in_group(
                update,
                f"✅ Order Completed: {target_state} (Auto)\nStats moved to Completed.",
            )
            return True
        except Exception as e:
            logger.error(f"更新订单完成统计数据失败（自动完成）: {e}", exc_info=True)
            # 统计数据更新失败，但收入明细已记录，需要手动修复或重新计算
            await reply_in_group(
                update,
                f"❌ Statistics update failed, but income record saved. Use /fix_statistics to repair. Error: {str(e)}",
            )
            return False

    else:
        # Normal <-> Overdue (都在 Valid 池中，仅状态变更)
        await reply_in_group(update, f"🔄 State Changed: {target_state} (Auto)")
        return True


async def _record_state_change_operation(
    update: Update,
    chat_id: int,
    order_id: str,
    current_state: str,
    target_state: str,
    group_id: str,
    amount: float,
) -> None:
    """记录状态变更操作历史

    Args:
        update: Telegram 更新对象
        chat_id: 聊天ID
        order_id: 订单ID
        current_state: 当前状态
        target_state: 目标状态
        group_id: 归属ID
        amount: 订单金额
    """
    user_id = update.effective_user.id if update.effective_user else 0

    try:
        from utils.date_helpers import get_daily_period_date

        # 根据状态变更类型确定操作类型
        operation_type = None
        operation_data = {
            "chat_id": chat_id,
            "order_id": order_id,
            "old_state": current_state,
            "new_state": target_state,
            "group_id": group_id,
            "amount": amount,
            "trigger": "auto_from_title",  # 标记为自动触发
        }

        if target_state == "end":
            operation_type = "order_completed"
            operation_data["date"] = get_daily_period_date()
        elif target_state == "breach_end":
            operation_type = "order_breach_end"
            operation_data["date"] = get_daily_period_date()
            operation_data["amount"] = amount
        else:
            operation_type = "order_state_change"

        # 记录操作历史
        await db_operations.record_operation(
            user_id=user_id,
            operation_type=operation_type,
            operation_data=operation_data,
            chat_id=chat_id,
        )

        logger.info(
            f"已记录自动状态变更操作历史: order_id={order_id}, {current_state} -> {target_state}, user_id={user_id}"
        )

    except Exception as e:
        # 记录操作历史失败不影响主流程，只记录日志
        logger.error(f"记录自动状态变更操作历史失败: {e}", exc_info=True)


def get_state_from_title(title: str) -> str:
    """从群名识别订单状态"""
    # 注意：需要先检查组合符号，再检查单个符号
    if "❌⭕️" in title:
        return "breach_end"
    elif "⭕️" in title:
        return "end"
    elif "❌" in title:
        return "breach"
    elif "❗️" in title:
        return "overdue"
    else:
        return "normal"


def _match_a_prefix_format(title: str) -> Optional[Dict[str, str]]:
    """匹配A前缀格式（A + 10或11位数字）

    Args:
        title: 群名

    Returns:
        如果匹配成功，返回包含 raw_digits, order_id, customer, is_11_digits 的字典
        否则返回 None
    """
    # 优先匹配11位数字
    match_11 = re.match(r"^A(\d{11})", title)
    if match_11:
        # 确保不是12位数字的前11位
        if len(title) > 12 and title[12].isdigit():
            match_11 = None
        else:
            raw_digits = match_11.group(1)
            return {
                "raw_digits": raw_digits,
                "order_id": "A" + raw_digits,
                "customer": "A",
                "is_11_digits": True,
            }

    # 匹配10位数字
    if not match_11:
        match_10 = re.match(r"^A(\d{10})", title)
        if match_10:
            # 确保不是11位数字的前10位
            if len(title) > 11 and title[11].isdigit():
                match_10 = None
            else:
                raw_digits = match_10.group(1)
                return {
                    "raw_digits": raw_digits,
                    "order_id": "A" + raw_digits,
                    "customer": "A",
                    "is_11_digits": False,
                }

    return None


def _match_traditional_format(title: str) -> Optional[Dict[str, str]]:
    """匹配传统格式（10或11位数字开头，可选A后缀）

    Args:
        title: 群名

    Returns:
        如果匹配成功，返回包含 raw_digits, order_id, customer, is_11_digits 的字典
        否则返回 None
    """
    # 优先匹配11位数字
    match_11 = re.match(r"^(\d{11})(A)?", title)
    if match_11:
        # 确保不是12位数字的前11位
        if len(title) > 11 and title[11].isdigit():
            match_11 = None
        else:
            raw_digits = match_11.group(1)
            has_a_suffix = match_11.group(2) == "A"
            return {
                "raw_digits": raw_digits,
                "order_id": raw_digits + "A" if has_a_suffix else raw_digits,
                "customer": "A" if has_a_suffix else "B",
                "is_11_digits": True,
            }

    # 匹配10位数字
    if not match_11:
        match_10 = re.match(r"^(\d{10})(A)?", title)
        if match_10:
            # 确保不是11位数字的前10位
            if len(title) > 10 and title[10].isdigit():
                match_10 = None
            else:
                raw_digits = match_10.group(1)
                has_a_suffix = match_10.group(2) == "A"
                return {
                    "raw_digits": raw_digits,
                    "order_id": raw_digits + "A" if has_a_suffix else raw_digits,
                    "customer": "A" if has_a_suffix else "B",
                    "is_11_digits": False,
                }

    return None


def _parse_date_from_digits(raw_digits: str) -> Optional[date]:
    """从数字字符串解析日期（前6位: YYMMDD）

    Args:
        raw_digits: 数字字符串（10或11位）

    Returns:
        解析后的日期对象，如果解析失败返回 None
    """
    date_part = raw_digits[:6]
    try:
        # 假设 20YY
        full_date_str = f"20{date_part}"
        return datetime.strptime(full_date_str, "%Y%m%d").date()
    except ValueError:
        return None


def _parse_amount_from_digits(raw_digits: str, is_11_digits: bool) -> float:
    """从数字字符串解析金额

    Args:
        raw_digits: 数字字符串（10或11位）
        is_11_digits: 是否为11位数字

    Returns:
        解析后的金额
    """
    if is_11_digits:
        # 11位数字: YYMMDDNNKKH
        # KK = 第9-10位 (千位)
        # H = 第11位 (百位)
        amount_thousands = int(raw_digits[8:10])
        amount_hundreds = int(raw_digits[10])
        return amount_thousands * 1000 + amount_hundreds * 100
    else:
        # 10位数字: YYMMDDNNKK
        # KK = 第9-10位 (千位)
        amount_part = raw_digits[8:10]
        return int(amount_part) * 1000


def parse_order_from_title(title: str) -> Optional[Dict[str, Union[str, date, float]]]:
    """从群名解析订单信息

    规则:
    1. 群名必须以10个或11个连续数字开始，或者以A开头后跟10或11个数字
    2. 10个数字格式: YYMMDDNNKK (YYMMDD=日期, NN=序号, KK=金额千位)
    3. 11个数字格式: YYMMDDNNKKH (YYMMDD=日期, NN=序号, KK=金额千位, H=金额百位)
    4. 最后带A表示新客户，否则为老客户
    5. 支持A开头的格式: A2310220105 (保持A前缀格式，order_id为A2310220105)
    6. 也支持A后缀格式: 2310220105A (保持A后缀格式，order_id为2310220105A)

    Args:
        title: 群名

    Returns:
        包含 date, amount, order_id, customer, full_date_str 的字典，如果解析失败返回 None
    """
    # 首先尝试匹配A前缀格式
    match_result = _match_a_prefix_format(title)
    if not match_result:
        # 尝试匹配传统格式
        match_result = _match_traditional_format(title)

    if not match_result:
        return None

    raw_digits = match_result["raw_digits"]
    order_id = match_result["order_id"]
    customer = match_result["customer"]
    is_11_digits = match_result["is_11_digits"]

    # 解析日期
    order_date_obj = _parse_date_from_digits(raw_digits)
    if not order_date_obj:
        return None

    # 解析金额
    amount = _parse_amount_from_digits(raw_digits, is_11_digits)

    # 构建完整日期字符串
    full_date_str = f"20{raw_digits[:6]}"

    return {
        "date": order_date_obj,
        "amount": amount,
        "order_id": order_id,
        "customer": customer,
        "full_date_str": full_date_str,
    }


async def update_order_state_from_title(
    update: Update, context: ContextTypes.DEFAULT_TYPE, order: Dict[str, Any], title: str
) -> None:
    """根据群名变更自动更新订单状态和日期信息

    此函数会在群名变更时自动执行以下操作：
    1. 解析群名中的日期信息
    2. 如果日期与订单当前日期不一致，自动更新订单日期和星期分组
    3. 根据群名中的状态标记更新订单状态

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        order: 订单字典，包含订单的所有信息
        title: 新的群名，用于解析订单信息和状态

    Note:
        - 已完成订单（end, breach_end）不会更新
        - 如果群名无法解析，只更新状态（如果状态标记存在）
        - 日期更新会同时更新 weekday_group 字段
    """
    current_state = order.get("state")
    if not current_state:
        logger.warning(f"订单缺少状态信息: {order.get('order_id', 'unknown')}")
        return

    # 获取基本信息
    chat_id = order.get("chat_id")
    group_id = order.get("group_id")
    amount = order.get("amount", 0)
    order_id = order.get("order_id", "unknown")

    if not chat_id:
        logger.error(f"订单缺少 chat_id: {order_id}")
        return

    # 归档订单保护：end 和 breach_end 状态的订单归档，不可更改任何数据
    if current_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 状态为 {current_state}（归档状态），跳过所有更新，保持数据不变"
        )
        return

    # 1. 解析群名，检查日期和星期分组是否需要更新
    parsed_info = parse_order_from_title(title)
    if parsed_info:
        new_order_date = parsed_info.get("date")
        if new_order_date:
            current_date_str = order.get("date", "")
            current_order_date = _parse_current_order_date(current_date_str)

            # 判断是否需要更新日期
            should_update_date = False
            if current_order_date:
                if new_order_date != current_order_date:
                    should_update_date = True
                    logger.info(
                        f"订单 {order_id} 群名日期变化: {current_order_date} -> {new_order_date}"
                    )
            else:
                # 当前日期无法解析，使用群名中的日期修复
                should_update_date = True
                logger.info(f"订单 {order_id} 数据库日期无效，使用群名中的日期: {new_order_date}")

            if should_update_date:
                await _update_order_date_and_weekday(order, chat_id, new_order_date, order_id)
            else:
                # 日期没有变化，但检查星期分组是否正确
                current_weekday_group = order.get("weekday_group", "")
                correct_weekday_group = get_weekday_group_from_date(new_order_date)

                if current_weekday_group != correct_weekday_group:
                    logger.info(
                        f"订单 {order_id} 星期分组不正确: {current_weekday_group} -> {correct_weekday_group}"
                    )
                    weekday_update_success = await db_operations.update_order_weekday_group(
                        chat_id, correct_weekday_group
                    )
                    if weekday_update_success:
                        order["weekday_group"] = correct_weekday_group
                        logger.info(
                            f"订单 {order_id} 星期分组已修正: {current_weekday_group} -> {correct_weekday_group}"
                        )
                    else:
                        logger.warning(
                            f"订单 {order_id} 星期分组更新失败: chat_id={chat_id}, "
                            f"correct_weekday_group={correct_weekday_group}"
                        )

    # 2. 处理状态变更
    target_state = get_state_from_title(title)
    if current_state == target_state:
        return

    # 验证状态转换是否合法
    if not _validate_state_transition(current_state, target_state, order_id):
        return

    try:
        # 使用 OrderService 统一处理状态转换
        from services.order_service import OrderService

        # 确定允许的旧状态
        allowed_old_states = ()
        if target_state == "normal":
            allowed_old_states = ("overdue",)
        elif target_state == "overdue":
            allowed_old_states = ("normal",)
        elif target_state == "breach":
            allowed_old_states = ("normal", "overdue")
        elif target_state == "end":
            # end 状态需要特殊处理，使用 complete_order
            allowed_old_states = ("normal", "overdue")
            user_id = update.effective_user.id if update.effective_user else None
            success, error_msg, operation_data = await OrderService.complete_order(chat_id, user_id)
            if success:
                await reply_in_group(
                    update,
                    f"✅ Order Completed: {target_state} (Auto)\nStats moved to Completed.",
                )
            else:
                logger.error(f"Auto complete order failed: {error_msg}")
                await reply_in_group(
                    update,
                    f"❌ Auto complete order failed: {error_msg}",
                )
            return

        # 对于 normal, overdue, breach 状态转换，使用 change_order_state
        if allowed_old_states:
            user_id = update.effective_user.id if update.effective_user else None
            success, error_msg, operation_data = await OrderService.change_order_state(
                chat_id=chat_id,
                new_state=target_state,
                allowed_old_states=allowed_old_states,
                user_id=user_id,
            )

            if success:
                # 发送成功消息
                if target_state == "breach":
                    await reply_in_group(
                        update, f"🔄 State Changed: {target_state} (Auto)\nStats moved to Breach."
                    )
                else:
                    await reply_in_group(update, f"🔄 State Changed: {target_state} (Auto)")
            else:
                logger.error(f"Auto update state failed: {error_msg}")
                await reply_in_group(
                    update,
                    f"❌ Auto state update failed: {error_msg}",
                )

    except Exception as e:
        logger.error(f"Auto update state failed: {e}", exc_info=True)


async def _handle_parse_error(update: Update, title: str, manual_trigger: bool) -> None:
    """处理群名解析错误，发送错误消息

    Args:
        update: Telegram 更新对象
        title: 群名
        manual_trigger: 是否手动触发
    """
    if not manual_trigger:
        logger.info(
            f"Group title '{title}' does not match order pattern (must start with 10 or 11 digits)."
        )
        return

    # 检查是否是数字位数问题
    digits_match = re.search(r"A?(\d+)", title)
    if digits_match:
        digits = digits_match.group(1)
        digits_count = len(digits)
        if digits_count < 10:
            # 群组只使用英文
            if is_group_chat(update):
                await update.message.reply_text(
                    f"❌ Invalid Group Title Format.\n\n"
                    f"Detected {digits_count} digits, but system requires 10 or 11 digits.\n\n"
                    f"Current title: {title}\n"
                    f"Digits part: {digits}\n\n"
                    f"Correct format:\n"
                    f"1. 10 digits: YYMMDDNNKK\n"
                    f"   - YYMMDD = Date (6 digits)\n"
                    f"   - NN = Sequence (2 digits)\n"
                    f"   - KK = Amount thousands (2 digits)\n"
                    f"2. 11 digits: YYMMDDNNKKH\n"
                    f"   - YYMMDD = Date (6 digits)\n"
                    f"   - NN = Sequence (2 digits)\n"
                    f"   - KK = Amount thousands (2 digits)\n"
                    f"   - H = Amount hundreds (1 digit)\n\n"
                    f"Examples:\n"
                    f"- A2512801030（5）！ (10 digits)\n"
                    f"- A25128010305（5）！ (11 digits)"
                )
            else:
                await update.message.reply_text(
                    f"❌ Invalid Group Title Format.\n\n"
                    f"检测到 {digits_count} 位数字，但系统要求 10 位或 11 位数字。\n\n"
                    f"当前标题: {title}\n"
                    f"数字部分: {digits}\n\n"
                    f"正确格式:\n"
                    f"1. 10位数字: YYMMDDNNKK\n"
                    f"   - YYMMDD = 日期 (6位)\n"
                    f"   - NN = 序号 (2位)\n"
                    f"   - KK = 金额千位 (2位)\n"
                    f"2. 11位数字: YYMMDDNNKKH\n"
                    f"   - YYMMDD = 日期 (6位)\n"
                    f"   - NN = 序号 (2位)\n"
                    f"   - KK = 金额千位 (2位)\n"
                    f"   - H = 金额百位 (1位)\n\n"
                    f"示例:\n"
                    f"- A2512801030（5）！ (10位)\n"
                    f"- A25128010305（5）！ (11位)"
                )
            return

    # 通用错误消息
    await update.message.reply_text(
        "❌ Invalid Group Title Format.\n"
        "Expected:\n"
        "1. Old Customer: 10 digits (e.g., 2501050105)\n"
        "   or 11 digits (e.g., 25010501055)\n"
        "2. New Customer: 10 digits + A (e.g., 2501050105A)\n"
        "   or 11 digits + A (e.g., 25010501055A)\n"
        "   or A + 10 digits (e.g., A2511280307)\n"
        "   or A + 11 digits (e.g., A25112803075)\n\n"
        "Format:\n"
        "- 10 digits: YYMMDDNNKK (Date+Seq+Amount thousands)\n"
        "- 11 digits: YYMMDDNNKKH (Date+Seq+Amount thousands+hundreds)\n"
        "- Title must start with 10 or 11 consecutive digits, or A\n\n"
        f"Current title: {title}"
    )


async def _get_existing_chat_title(chat_id: int) -> Optional[str]:
    """获取现有群组的标题

    Args:
        chat_id: 群组ID

    Returns:
        群组标题，如果获取失败返回 None
    """
    try:
        from telegram import Bot

        from config import BOT_TOKEN

        bot = Bot(token=BOT_TOKEN)
        existing_chat = await bot.get_chat(chat_id)
        existing_title = existing_chat.title
        await bot.close()
        return existing_title
    except Exception as e:
        logger.warning(f"无法获取现有订单的群组标题 (chat_id: {chat_id}): {e}")
        return None


async def _associate_order_to_group(
    update: Update,
    order_id: str,
    existing_chat_id: int,
    new_chat_id: int,
    existing_state: str,
    manual_trigger: bool,
) -> Tuple[bool, Optional[Dict]]:
    """关联订单到新群组

    Args:
        update: Telegram 更新对象
        order_id: 订单ID
        existing_chat_id: 现有群组ID
        new_chat_id: 新群组ID
        existing_state: 现有订单状态
        manual_trigger: 是否手动触发

    Returns:
        Tuple[是否成功, 更新后的订单字典]
    """
    # 完成和违约完成的订单允许关联或创建新订单
    if existing_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 已完成（状态: {existing_state}），"
            f"允许关联到当前群组或创建新订单（chat_id: {existing_chat_id} -> {new_chat_id}）"
        )
        # 继续执行关联逻辑，不阻止

    # 更新订单的 chat_id 为当前群组（关联操作）
    logger.info(f"关联订单 {order_id} 到群组: (chat_id {existing_chat_id} -> {new_chat_id})")
    success = await db_operations.update_order_chat_id(order_id, new_chat_id)
    if success:
        if manual_trigger:
            if is_group_chat(update):
                await update.message.reply_text(
                    f"✅ Order {order_id} has been associated to current group"
                )
            else:
                await update.message.reply_text(f"✅ 订单 {order_id} 已关联到当前群组")
        # 获取更新后的订单
        updated_order = await db_operations.get_order_by_order_id(order_id)
        return True, updated_order
    else:
        if manual_trigger:
            if is_group_chat(update):
                await update.message.reply_text("❌ Failed to associate order")
            else:
                await update.message.reply_text("❌ 订单关联失败")
        return False, None


async def _update_existing_order_from_parsed_info(
    update: Update,
    chat_id: int,
    existing_order: Dict[str, Any],
    parsed_info: Dict[str, Any],
    title: str,
) -> bool:
    """更新现有订单的信息

    Args:
        update: Telegram 更新对象
        chat_id: 群组ID
        existing_order: 现有订单字典
        parsed_info: 解析后的订单信息
        title: 群名

    Returns:
        是否成功更新
    """
    order_id = parsed_info["order_id"]
    order_date = parsed_info["date"]
    amount = parsed_info["amount"]
    customer = parsed_info["customer"]

    # 获取状态
    initial_state = get_state_from_title(title)

    # 准备更新数据
    update_data = {
        "order_id": order_id,
        "date": order_date,
        "customer": customer,
        "amount": amount,
        "state": initial_state,
    }

    # 更新订单
    success = await db_operations.update_order_from_parsed_info(chat_id, update_data)

    if success:
        # 处理状态转换（如果状态变化）
        old_state = existing_order.get("state")
        if old_state != initial_state:
            # 验证状态转换是否合法
            if _validate_state_transition(old_state, initial_state, order_id):
                # 处理统计数据迁移
                group_id = existing_order.get("group_id", "S01")
                await _handle_state_transition_stats(
                    update, old_state, initial_state, existing_order, group_id, amount
                )

                # 记录操作历史
                await _record_state_change_operation(
                    update, chat_id, order_id, old_state, initial_state, group_id, amount
                )

        if is_group_chat(update):
            await update.message.reply_text("✅ Order updated")
        else:
            await update.message.reply_text("✅ 订单已更新")
        return True
    else:
        if is_group_chat(update):
            await update.message.reply_text("❌ Failed to update order")
        else:
            await update.message.reply_text("❌ 订单更新失败")
        return False


async def _create_new_order_internal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    parsed_info: Dict[str, Any],
    title: str,
) -> bool:
    """创建新订单的内部逻辑

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        chat_id: 群组ID
        parsed_info: 解析后的订单信息
        title: 群名

    Returns:
        是否成功创建
    """
    order_date = parsed_info["date"]
    amount = parsed_info["amount"]
    order_id = parsed_info["order_id"]
    customer = parsed_info["customer"]

    # 初始状态识别 (根据群名标志)
    initial_state = get_state_from_title(title)

    # 检查日期阈值 (2025-11-28)
    # 规则: 2025-11-28之前的订单作为历史数据导入，不扣款，不播报
    threshold_date = date(*HISTORICAL_THRESHOLD_DATE)
    is_historical = order_date < threshold_date

    # 检查余额 (仅当非历史订单时检查)
    if not is_historical:
        financial_data = await db_operations.get_financial_data()
        if financial_data["liquid_funds"] < amount:
            msg = (
                f"❌ Insufficient Liquid Funds\n"
                f"Current Balance: {financial_data['liquid_funds']:.2f}\n"
                f"Required: {amount:.2f}\n"
                f"Missing: {amount - financial_data['liquid_funds']:.2f}"
            )
            if is_group_chat(update):
                await update.message.reply_text(msg)
            return False

    group_id = "S01"  # 默认归属
    # 根据订单日期确定星期分组（历史订单和正常订单都使用订单日期）
    weekday_group = get_weekday_group_from_date(order_date)

    logger.info(
        f"创建订单 {order_id}: 日期={order_date}, 星期分组={weekday_group}, "
        f"weekday()={order_date.weekday()}"
    )

    # 构造创建时间
    created_at = f"{order_date.strftime('%Y-%m-%d')} 12:00:00"

    # 使用Pydantic验证订单数据
    try:
        # 验证金额
        amount_validated = validate_amount(amount)

        # 创建订单模型
        order_model = OrderCreateModel(
            order_id=order_id,
            group_id=group_id,
            chat_id=chat_id,
            date=created_at,
            weekday_group=weekday_group,
            customer=customer,
            amount=amount_validated,
            state=initial_state,
        )

        # 转换为字典（用于数据库操作）
        new_order = order_model.to_dict()

        logger.info(
            f"准备插入订单 {order_id}: weekday_group={new_order['weekday_group']}, date={new_order['date']}"
        )
    except ValueError as e:
        logger.error(f"订单数据验证失败: {e}", exc_info=True)
        if is_group_chat(update):
            await update.message.reply_text(f"❌ Order validation failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"创建订单模型失败: {e}", exc_info=True)
        if is_group_chat(update):
            await update.message.reply_text("❌ Failed to create order model.")
        return False

    # 创建订单（同时插入主表和所有分类表）
    if not await db_operations.create_order_in_classified_tables(new_order):
        if is_group_chat(update):
            await update.message.reply_text("❌ Failed to create order. Order ID might duplicate.")
        return False

    # 更新统计
    # 根据初始状态决定计入 Valid 还是 Breach
    is_initial_breach = initial_state == "breach"

    # 更新订单统计
    # 历史违约订单：只更新全局和分组统计，不更新日结统计
    if is_initial_breach:
        if is_historical:
            # 历史违约订单：跳过日结更新
            await update_all_stats("breach", amount, 1, group_id, skip_daily=True)
        else:
            # 非历史违约订单：正常更新（包括日结）
            await update_all_stats("breach", amount, 1, group_id)
    else:
        await update_all_stats("valid", amount, 1, group_id)

    # 非历史订单才扣款和更新客户统计
    if not is_historical:
        # 扣除流动资金
        await update_liquid_capital(-amount)

        # 客户统计
        client_field = "new_clients" if customer == "A" else "old_clients"
        await update_all_stats(client_field, amount, 1, group_id)

        # 自动播报下一期还款（基于订单日期计算下个周期）
        await send_auto_broadcast(update, context, chat_id, amount, created_at)
    else:
        # 历史订单不播报
        logger.info(f"Historical order {order_id} created, skipping broadcast")

    # 构建并发送确认消息
    msg = build_order_creation_message(
        order_id=order_id,
        group_id=group_id,
        created_at=created_at,
        weekday_group=weekday_group,
        customer=customer,
        amount=amount,
        initial_state=initial_state,
        is_historical=is_historical,
    )
    await update.message.reply_text(msg)

    # 记录操作历史（用于撤销）
    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        from handlers.undo_handlers import reset_undo_count

        await db_operations.record_operation(
            user_id=user_id,
            operation_type="order_created",
            operation_data={
                "order_id": order_id,
                "chat_id": chat_id,
                "group_id": group_id,
                "amount": amount,
                "customer": customer,
                "initial_state": initial_state,
                "is_historical": is_historical,
                "date": created_at,
            },
            chat_id=chat_id,
        )
        # 重置撤销计数
        if context:
            reset_undo_count(context, user_id)

    return True


async def try_create_order_from_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat,
    title: str,
    manual_trigger: bool = False,
    allow_create_new: bool = True,
):
    """尝试从群标题创建订单（通用逻辑）

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        chat: 聊天对象
        title: 群名
        manual_trigger: 是否手动触发
        allow_create_new: 是否允许创建新订单（False 时只关联，不创建）
    """
    chat_id = chat.id

    logger.info(
        f"Attempting to create order from title: '{title}' (chat_id: {chat_id}, manual_trigger: {manual_trigger})"
    )

    # 1. 解析群名 (ID, Customer, Date, Amount)
    parsed_info = parse_order_from_title(title)
    if not parsed_info:
        if manual_trigger:
            # 检查是否是数字位数问题
            digits_match = re.search(r"A?(\d+)", title)
            if digits_match:
                digits = digits_match.group(1)
                digits_count = len(digits)
                if digits_count < 10:
                    # 群组只使用英文
                    if is_group_chat(update):
                        await update.message.reply_text(
                            f"❌ Invalid Group Title Format.\n\n"
                            f"Detected {digits_count} digits, but system requires 10 or 11 digits.\n\n"
                            f"Current title: {title}\n"
                            f"Digits part: {digits}\n\n"
                            f"Correct format:\n"
                            f"1. 10 digits: YYMMDDNNKK\n"
                            f"   - YYMMDD = Date (6 digits)\n"
                            f"   - NN = Sequence (2 digits)\n"
                            f"   - KK = Amount thousands (2 digits)\n"
                            f"2. 11 digits: YYMMDDNNKKH\n"
                            f"   - YYMMDD = Date (6 digits)\n"
                            f"   - NN = Sequence (2 digits)\n"
                            f"   - KK = Amount thousands (2 digits)\n"
                            f"   - H = Amount hundreds (1 digit)\n\n"
                            f"Examples:\n"
                            f"- A2512801030（5）！ (10 digits)\n"
                            f"- A25128010305（5）！ (11 digits)"
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ Invalid Group Title Format.\n\n"
                            f"检测到 {digits_count} 位数字，但系统要求 10 位或 11 位数字。\n\n"
                            f"当前标题: {title}\n"
                            f"数字部分: {digits}\n\n"
                            f"正确格式:\n"
                            f"1. 10位数字: YYMMDDNNKK\n"
                            f"   - YYMMDD = 日期 (6位)\n"
                            f"   - NN = 序号 (2位)\n"
                            f"   - KK = 金额千位 (2位)\n"
                            f"2. 11位数字: YYMMDDNNKKH\n"
                            f"   - YYMMDD = 日期 (6位)\n"
                            f"   - NN = 序号 (2位)\n"
                            f"   - KK = 金额千位 (2位)\n"
                            f"   - H = 金额百位 (1位)\n\n"
                            f"示例:\n"
                            f"- A2512801030（5）！ (10位)\n"
                            f"- A25128010305（5）！ (11位)"
                        )
                else:
                    await update.message.reply_text(
                        "❌ Invalid Group Title Format.\n"
                        "Expected:\n"
                        "1. Old Customer: 10 digits (e.g., 2501050105)\n"
                        "   or 11 digits (e.g., 25010501055)\n"
                        "2. New Customer: 10 digits + A (e.g., 2501050105A)\n"
                        "   or 11 digits + A (e.g., 25010501055A)\n"
                        "   or A + 10 digits (e.g., A2511280307)\n"
                        "   or A + 11 digits (e.g., A25112803075)\n\n"
                        "Format:\n"
                        "- 10 digits: YYMMDDNNKK (Date+Seq+Amount thousands)\n"
                        "- 11 digits: YYMMDDNNKKH (Date+Seq+Amount thousands+hundreds)\n"
                        "- Title must start with 10 or 11 consecutive digits, or A\n\n"
                        f"Current title: {title}"
                    )
            else:
                await update.message.reply_text(
                    "❌ Invalid Group Title Format.\n"
                    "Expected:\n"
                    "1. Old Customer: 10 digits (e.g., 2501050105)\n"
                    "   or 11 digits (e.g., 25010501055)\n"
                    "2. New Customer: 10 digits + A (e.g., 2501050105A)\n"
                    "   or 11 digits + A (e.g., 25010501055A)\n"
                    "   or A + 10 digits (e.g., A2511280307)\n"
                    "   or A + 11 digits (e.g., A25112803075)\n\n"
                    "Format:\n"
                    "- 10 digits: YYMMDDNNKK (Date+Seq+Amount thousands)\n"
                    "- 11 digits: YYMMDDNNKKH (Date+Seq+Amount thousands+hundreds)\n"
                    "- Title must start with 10 or 11 consecutive digits, or A\n\n"
                    f"Current title: {title}"
                )
        else:
            logger.info(
                f"Group title '{title}' does not match order pattern (must start with 10 or 11 digits)."
            )
        return

    logger.info(
        f"Parsed order info: order_id={parsed_info['order_id']}, customer={parsed_info['customer']}, date={parsed_info['date']}, amount={parsed_info['amount']}"
    )

    # 2. 提取信息
    order_date = parsed_info["date"]
    amount = parsed_info["amount"]
    order_id = parsed_info["order_id"]
    customer = parsed_info["customer"]  # 'A' or 'B'

    # 3. 优先根据群组标题查找订单（群组标题优先比对）
    # 订单号是以群组标题为标准建立的，所以应该先比对群组标题
    existing_order_by_id = await db_operations.get_order_by_order_id(order_id)
    if existing_order_by_id:
        existing_chat_id = existing_order_by_id.get("chat_id")
        existing_state = existing_order_by_id.get("state")

        # 通过 Telegram API 获取现有订单的群组标题，用于比较（群组标题优先）
        existing_title = None
        try:
            from telegram import Bot

            from config import BOT_TOKEN

            bot = Bot(token=BOT_TOKEN)
            existing_chat = await bot.get_chat(existing_chat_id)
            existing_title = existing_chat.title
            await bot.close()
        except Exception as e:
            logger.warning(f"无法获取现有订单的群组标题 (chat_id: {existing_chat_id}): {e}")

        # 群组标题优先比对：如果群组标题相同，说明是同一个订单，应该关联
        if existing_title and existing_title == title:
            # 群组标题相同，说明是同一个订单，更新 chat_id（如果不同）
            logger.info(
                f"订单 {order_id} 群组标题匹配: '{existing_title}' = '{title}', "
                f"更新 chat_id: {existing_chat_id} -> {chat_id}"
            )
            if existing_chat_id != chat_id:
                success = await db_operations.update_order_chat_id(order_id, chat_id)
                if success:
                    existing_order_by_id["chat_id"] = chat_id
                else:
                    if manual_trigger:
                        if is_group_chat(update):
                            await update.message.reply_text("❌ Failed to update order chat_id")
                        else:
                            await update.message.reply_text("❌ 订单 chat_id 更新失败")
                    return
            # 使用该订单继续处理
            existing_order = existing_order_by_id
        elif existing_chat_id != chat_id:
            # 群组标题不同且 chat_id 不同，需要关联到当前群组
            if existing_state in ["end", "breach_end"]:
                # 完成和违约完成的订单允许关联或创建新订单
                logger.info(
                    f"订单 {order_id} 已完成（状态: {existing_state}），"
                    f"允许关联到当前群组或创建新订单（chat_id: {existing_chat_id} -> {chat_id}）"
                )
                # 继续执行关联或创建新订单的逻辑

            # 更新订单的 chat_id 为当前群组（关联操作）
            logger.info(
                f"关联订单 {order_id} 到群组: 原群组标题='{existing_title}', 新群组标题='{title}' "
                f"(chat_id {existing_chat_id} -> {chat_id})"
            )
            success = await db_operations.update_order_chat_id(order_id, chat_id)
            if success:
                if manual_trigger:
                    if is_group_chat(update):
                        await update.message.reply_text(
                            f"✅ Order {order_id} has been associated to current group"
                        )
                    else:
                        await update.message.reply_text(f"✅ 订单 {order_id} 已关联到当前群组")
                # 关联成功后直接返回，不继续执行后续更新逻辑
                # 关联操作只是将订单关联到新群组，不应该触发订单信息更新
                return
            else:
                if manual_trigger:
                    if is_group_chat(update):
                        await update.message.reply_text("❌ Failed to associate order")
                    else:
                        await update.message.reply_text("❌ 订单关联失败")
                return
        else:
            # 订单已在当前群组（chat_id 相同），使用现有订单
            existing_order = existing_order_by_id
    else:
        # 订单不存在，检查当前群组是否已有其他订单
        existing_order = await db_operations.get_order_by_chat_id_including_archived(chat_id)

    # 4. 处理已存在的订单
    if existing_order:
        current_state = existing_order.get("state")
        existing_order_id = existing_order.get("order_id")

        # 如果订单已归档（end 或 breach_end），允许创建新订单
        if current_state in ["end", "breach_end"]:
            # 完成和违约完成的订单不归档，允许创建新订单
            logger.info(
                f"订单 {existing_order_id} 已完成（状态: {current_state}），"
                f"允许创建新订单 {order_id}（chat_id: {chat_id}）"
            )
            # 继续执行创建新订单的逻辑（跳过下面的 elif 分支）

        # 如果是手动触发且订单未归档，根据订单日期决定是更新还是创建新订单
        if manual_trigger and current_state not in ["end", "breach_end"]:
            # 检查订单日期：如果日期 >= 订单创建阈值日期，创建新订单；否则更新现有订单
            from constants import ORDER_CREATE_CUTOFF_DATE

            cutoff_date = date(*ORDER_CREATE_CUTOFF_DATE)
            if order_date >= cutoff_date:
                # 日期在26号以后（包括26号），创建新订单
                logger.info(
                    f"订单日期 {order_date} >= {cutoff_date}，创建新订单而不是更新（chat_id: {chat_id}）"
                )
                # 继续执行创建新订单的逻辑
            else:
                # 日期在26号之前，更新现有订单
                logger.info(
                    f"订单日期 {order_date} < {cutoff_date}，更新现有订单（chat_id: {chat_id}）"
                )

                # 检查现有订单是否是已完成或违约完成状态
                # 完成和违约完成的订单允许创建新订单，不阻止
                if current_state in ["end", "breach_end"]:
                    logger.info(
                        f"订单 {existing_order_id} 已完成（状态: {current_state}），"
                        f"允许创建新订单而不是覆盖（chat_id: {chat_id}）"
                    )
                    # 继续执行创建新订单的逻辑，不返回

                # 获取状态
                initial_state = get_state_from_title(title)

                # 准备更新数据
                update_data = {
                    "order_id": order_id,
                    "date": order_date,
                    "customer": customer,
                    "amount": amount,
                    "state": initial_state,
                }

                # 更新订单
                success = await db_operations.update_order_from_parsed_info(chat_id, update_data)

                if success:
                    # 处理状态转换（如果状态变化）
                    old_state = existing_order.get("state")
                    if old_state != initial_state:
                        # 验证状态转换是否合法
                        if _validate_state_transition(old_state, initial_state, order_id):
                            # 处理统计数据迁移
                            group_id = existing_order.get("group_id", "S01")
                            await _handle_state_transition_stats(
                                update, old_state, initial_state, existing_order, group_id, amount
                            )

                            # 记录操作历史
                            await _record_state_change_operation(
                                update,
                                chat_id,
                                order_id,
                                old_state,
                                initial_state,
                                group_id,
                                amount,
                            )

                    if is_group_chat(update):
                        await update.message.reply_text("✅ Order updated")
                    else:
                        await update.message.reply_text("✅ 订单已更新")
                else:
                    if is_group_chat(update):
                        await update.message.reply_text("❌ Failed to update order")
                    else:
                        await update.message.reply_text("❌ 订单更新失败")
                return
        else:
            # 如果是自动触发（改名），则尝试更新状态
            await update_order_state_from_title(update, context, existing_order, title)
            return

    # 5. 如果订单不存在且不允许创建新订单，提示失败
    if not allow_create_new:
        if manual_trigger:
            await update.message.reply_text(
                f"❌ 订单 {order_id} 不存在，无法关联。\n" f"请使用 /create 命令创建新订单。"
            )
        return

    # 6. 初始状态识别 (根据群名标志)
    initial_state = get_state_from_title(title)

    # 7. 检查日期阈值 (2025-11-28)
    # 规则: 2025-11-28之前的订单作为历史数据导入，不扣款，不播报
    threshold_date = date(*HISTORICAL_THRESHOLD_DATE)
    is_historical = order_date < threshold_date

    # 检查余额 (仅当非历史订单时检查)
    if not is_historical:
        financial_data = await db_operations.get_financial_data()
        if financial_data["liquid_funds"] < amount:
            msg = (
                f"❌ Insufficient Liquid Funds\n"
                f"Current Balance: {financial_data['liquid_funds']:.2f}\n"
                f"Required: {amount:.2f}\n"
                f"Missing: {amount - financial_data['liquid_funds']:.2f}"
            )
            if manual_trigger or is_group_chat(update):
                await update.message.reply_text(msg)
            return

    group_id = "S01"  # 默认归属
    # 根据订单日期确定星期分组（历史订单和正常订单都使用订单日期）
    weekday_group = get_weekday_group_from_date(order_date)

    # 添加调试日志，确保星期分组计算正确
    logger.info(
        f"创建订单 {order_id}: 日期={order_date}, 星期分组={weekday_group}, "
        f"weekday()={order_date.weekday()}"
    )

    # 构造创建时间
    created_at = f"{order_date.strftime('%Y-%m-%d')} 12:00:00"

    # 使用Pydantic验证订单数据
    try:
        # 验证金额
        amount_validated = validate_amount(amount)

        # 创建订单模型
        order_model = OrderCreateModel(
            order_id=order_id,
            group_id=group_id,
            chat_id=chat_id,
            date=created_at,
            weekday_group=weekday_group,
            customer=customer,
            amount=amount_validated,
            state=initial_state,
        )

        # 转换为字典（用于数据库操作）
        new_order = order_model.to_dict()

        # 添加调试日志，确认插入数据库的值
        logger.info(
            f"准备插入订单 {order_id}: weekday_group={new_order['weekday_group']}, date={new_order['date']}"
        )
    except ValueError as e:
        logger.error(f"订单数据验证失败: {e}", exc_info=True)
        if manual_trigger:
            await update.message.reply_text(f"❌ Order validation failed: {str(e)}")
        return
    except Exception as e:
        logger.error(f"创建订单模型失败: {e}", exc_info=True)
        if manual_trigger:
            await update.message.reply_text("❌ Failed to create order model.")
        return

    # 6. 创建订单（同时插入主表和所有分类表）
    if not await db_operations.create_order_in_classified_tables(new_order):
        if manual_trigger:
            await update.message.reply_text("❌ Failed to create order. Order ID might duplicate.")
        return

    # 7. 更新统计
    # 根据初始状态决定计入 Valid 还是 Breach
    is_initial_breach = initial_state == "breach"

    # 更新订单统计
    # 历史违约订单：只更新全局和分组统计，不更新日结统计
    if is_initial_breach:
        if is_historical:
            # 历史违约订单：跳过日结更新
            await update_all_stats("breach", amount, 1, group_id, skip_daily=True)
        else:
            # 非历史违约订单：正常更新（包括日结）
            await update_all_stats("breach", amount, 1, group_id)
    else:
        await update_all_stats("valid", amount, 1, group_id)

    # 非历史订单才扣款和更新客户统计
    if not is_historical:
        # 扣除流动资金
        await update_liquid_capital(-amount)

        # 客户统计
        client_field = "new_clients" if customer == "A" else "old_clients"
        await update_all_stats(client_field, amount, 1, group_id)

        # 自动播报下一期还款（基于订单日期计算下个周期）
        await send_auto_broadcast(update, context, chat_id, amount, created_at)
    else:
        # 历史订单不播报
        logger.info(f"Historical order {order_id} created, skipping broadcast")

    # 构建并发送确认消息
    msg = build_order_creation_message(
        order_id=order_id,
        group_id=group_id,
        created_at=created_at,
        weekday_group=weekday_group,
        customer=customer,
        amount=amount,
        initial_state=initial_state,
        is_historical=is_historical,
    )
    await update.message.reply_text(msg)

    # 记录操作历史（用于撤销）
    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        from handlers.undo_handlers import reset_undo_count

        await db_operations.record_operation(
            user_id=user_id,
            operation_type="order_created",
            operation_data={
                "order_id": order_id,
                "chat_id": chat_id,
                "group_id": group_id,
                "amount": amount,
                "customer": customer,
                "initial_state": initial_state,
                "is_historical": is_historical,
                "date": created_at,
            },
            chat_id=chat_id,
        )
        # 重置撤销计数
        if context:
            reset_undo_count(context, user_id)


async def send_auto_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    amount: float,
    order_date: str = None,
):
    """订单创建后自动播报下一期还款（无中文，带内联键盘）"""
    try:
        # 计算本金和本金12%
        principal = amount
        principal_12 = principal * 0.12

        # 获取未付利息（新订单默认为0）
        outstanding_interest = 0

        # 使用统一的播报模板函数，基于订单日期计算下个周期
        from utils.broadcast_helpers import calculate_next_payment_date, format_broadcast_message

        _, date_str, weekday_str = calculate_next_payment_date(order_date)
        message = format_broadcast_message(
            principal=principal,
            principal_12=principal_12,
            outstanding_interest=outstanding_interest,
            date_str=date_str,
            weekday_str=weekday_str,
        )

        # 获取群组消息配置（用于获取机器人链接和人工链接）
        config = await db_operations.get_group_message_config_by_chat_id(chat_id)
        bot_links = config.get("bot_links") if config else None
        worker_links = config.get("worker_links") if config else None

        # 创建内联键盘（无中文）
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        # 解析机器人链接
        bot_link_list = []
        if bot_links:
            bot_link_list = [
                link.strip()
                for link in bot_links.split("\n")
                if link.strip()
                and (link.strip().startswith("http://") or link.strip().startswith("https://"))
            ]

        # 解析人工链接
        worker_link_list = []
        if worker_links:
            worker_link_list = [
                link.strip()
                for link in worker_links.split("\n")
                if link.strip()
                and (link.strip().startswith("http://") or link.strip().startswith("https://"))
            ]

        # 添加机器人链接按钮（无中文）
        if bot_link_list:
            keyboard.append([InlineKeyboardButton("Bot", url=bot_link_list[0])])

        # 添加人工链接按钮（无中文）
        if worker_link_list:
            keyboard.append([InlineKeyboardButton("Worker", url=worker_link_list[0])])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        # 发送消息（带内联键盘）
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=reply_markup,
        )
        logger.info(f"自动播报已发送到群组 {chat_id}（带内联键盘）")
    except Exception as e:
        logger.error(f"自动播报失败: {e}", exc_info=True)
        # 不显示错误给用户，静默失败

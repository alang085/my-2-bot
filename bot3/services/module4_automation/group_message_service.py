"""群组消息服务 - 精简版：只保留核心功能"""

import logging
from typing import Optional, Tuple

import db_operations

logger = logging.getLogger(__name__)


class GroupMessageService:
    """群组消息业务服务 - 精简版"""

    @staticmethod
    async def save_config(
        chat_id: int,
        chat_title: Optional[str] = None,
        is_active: Optional[int] = None,
        bot_links: Optional[str] = None,
        worker_links: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """保存群组消息配置（用于设置链接等）"""
        try:
            success = await db_operations.save_group_message_config(
                chat_id=chat_id,
                chat_title=chat_title,
                is_active=is_active,
                bot_links=bot_links,
                worker_links=worker_links,
            )
            return (True, None) if success else (False, "❌ 保存失败")
        except Exception as e:
            logger.error(f"保存群组消息配置失败: {e}", exc_info=True)
            return False, f"❌ 保存失败: {str(e)}"

    @staticmethod
    async def setup_group_auto(
        chat_id: int, chat_title: str
    ) -> Tuple[bool, Optional[str]]:
        """一键设置群组自动消息功能（自动配置默认文案）"""
        try:
            # 确保数据库中有默认的宣传语录（宣传消息仍使用语录表轮播）
            await GroupMessageService.ensure_default_promotion_messages()

            # 检查是否已存在配置
            existing_config = await db_operations.get_group_message_config_by_chat_id(
                chat_id
            )

            # 获取默认文案
            try:
                default_messages = GroupMessageService._get_default_weekday_messages()
                logger.info(f"获取默认文案成功，共 {len(default_messages)} 个字段")
            except Exception as e:
                logger.error(f"获取默认文案失败: {e}", exc_info=True)
                return False, f"❌ 获取默认文案失败: {str(e)}"

            # 保存群组配置（包含默认文案）
            try:
                success = await db_operations.save_group_message_config(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    is_active=1,
                    **default_messages,  # 传入所有默认文案字段
                )
                logger.info(f"保存群组配置成功: chat_id={chat_id}, success={success}")
            except Exception as e:
                logger.error(f"保存群组配置失败: {e}", exc_info=True)
                import traceback

                logger.error(f"详细错误: {traceback.format_exc()}")
                return False, f"❌ 保存配置失败: {str(e)}"

            if not existing_config:
                # 新群组：开启全局公告计划
                await db_operations.save_announcement_schedule(
                    interval_hours=3, is_active=1
                )

            return (True, None) if success else (False, "❌ 开启失败")
        except AttributeError as e:
            logger.error(f"AttributeError in setup_group_auto: {e}", exc_info=True)
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            return False, f"❌ AttributeError: {str(e)}"
        except Exception as e:
            logger.error(f"设置群组自动消息失败: {e}", exc_info=True)
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            return False, f"❌ 设置失败: {str(e)}"

    @staticmethod
    def _get_default_start_work_messages() -> dict:
        """获取默认开工消息（周一到周日）"""
        return {
            "start_work_message_1": "🌅 Good morning! We are now OPEN for business. / 早安！我们现在开始营业了。",
            "start_work_message_2": (
                "🚀 Service started! Ready to process your orders. "
                "/ 业务已开启！准备好处理您的订单。"
            ),
            "start_work_message_3": "✨ We are back online! Feel free to contact us. / 我们已上线！欢迎联系。",
            "start_work_message_4": "🌅 Good morning! We are now OPEN for business. / 早安！我们现在开始营业了。",
            "start_work_message_5": (
                "🚀 Service started! Ready to process your orders. "
                "/ 业务已开启！准备好处理您的订单。"
            ),
            "start_work_message_6": "✨ We are back online! Feel free to contact us. / 我们已上线！欢迎联系。",
            "start_work_message_7": "🌅 Good morning! We are now OPEN for business. / 早安！我们现在开始营业了。",
        }

    def _get_default_end_work_messages() -> dict:
        """获取默认收工消息（周一到周日）"""
        return {
            "end_work_message_1": "🌙 We are now CLOSED. See you tomorrow! / 我们现在收工了。明天见！",
            "end_work_message_2": (
                "💤 Business ended for today. All pending will be processed tomorrow. "
                "/ 今日营业结束。余下的明天处理。"
            ),
            "end_work_message_3": "👋 Offline now. Thank you for your support! / 已下线。感谢您的支持！",
            "end_work_message_4": "🌙 We are now CLOSED. See you tomorrow! / 我们现在收工了。明天见！",
            "end_work_message_5": (
                "💤 Business ended for today. All pending will be processed tomorrow. "
                "/ 今日营业结束。余下的明天处理。"
            ),
            "end_work_message_6": "👋 Offline now. Thank you for your support! / 已下线。感谢您的支持！",
            "end_work_message_7": "🌙 We are now CLOSED. See you tomorrow! / 我们现在收工了。明天见！",
        }

    def _get_default_welcome_messages() -> dict:
        """获取默认欢迎消息（周一到周日）"""
        return {
            "welcome_message_1": "👋 Welcome! We are glad to have you here. / 欢迎加入！我们很高兴您的到来。",
            "welcome_message_2": (
                "🎉 Welcome to our group! Feel free to contact us anytime. "
                "/ 欢迎加入我们的群组！随时欢迎联系我们。"
            ),
            "welcome_message_3": "🌟 Welcome! Our service is ready for you. / 欢迎！我们的服务为您准备好了。",
            "welcome_message_4": "👋 Welcome! We are glad to have you here. / 欢迎加入！我们很高兴您的到来。",
            "welcome_message_5": (
                "🎉 Welcome to our group! Feel free to contact us anytime. "
                "/ 欢迎加入我们的群组！随时欢迎联系我们。"
            ),
            "welcome_message_6": "🌟 Welcome! Our service is ready for you. / 欢迎！我们的服务为您准备好了。",
            "welcome_message_7": "👋 Welcome! We are glad to have you here. / 欢迎加入！我们很高兴您的到来。",
        }

    def _get_default_anti_fraud_messages() -> dict:
        """获取默认防诈骗消息（周一到周日）"""
        return {
            "anti_fraud_message_1": (
                "⚠️ PLEASE NOTE: Only contact our official staff links! "
                "/ 请注意：只联系我们的官方员工链接！"
            ),
            "anti_fraud_message_2": (
                "🚫 DO NOT trust anyone who messages you first! "
                "/ 不要相信任何主动联系你的人！"
            ),
            "anti_fraud_message_3": (
                "🔒 Protect your funds! Verify the ID before payment. "
                "/ 保护您的资金！付款前核对ID。"
            ),
            "anti_fraud_message_4": (
                "⚠️ PLEASE NOTE: Only contact our official staff links! "
                "/ 请注意：只联系我们的官方员工链接！"
            ),
            "anti_fraud_message_5": (
                "🚫 DO NOT trust anyone who messages you first! "
                "/ 不要相信任何主动联系你的人！"
            ),
            "anti_fraud_message_6": (
                "🔒 Protect your funds! Verify the ID before payment. "
                "/ 保护您的资金！付款前核对ID。"
            ),
            "anti_fraud_message_7": (
                "⚠️ PLEASE NOTE: Only contact our official staff links! "
                "/ 请注意：只联系我们的官方员工链接！"
            ),
        }

    @staticmethod
    def _get_default_weekday_messages() -> dict:
        """获取默认的周一到周日文案（7天）"""
        messages = {}
        messages.update(GroupMessageService._get_default_start_work_messages())
        messages.update(GroupMessageService._get_default_end_work_messages())
        messages.update(GroupMessageService._get_default_welcome_messages())
        messages.update(GroupMessageService._get_default_anti_fraud_messages())
        return messages

    @staticmethod
    async def ensure_default_promotion_messages():
        """确保数据库中有默认的宣传语录（仅用于宣传消息轮播）"""
        try:
            # 宣传消息仍然使用语录表进行轮播
            if not await db_operations.get_active_promotion_messages():
                defaults = [
                    "📢 Safe and fast service. Trust us with your needs! / 安全快速的服务。信赖我们！",
                    "💰 Best rates in town! Contact our staff now. / 全城最优利率！立即联系员工。",
                    "⚡️ Quick processing, no delay! / 快速处理，绝不拖延！",
                ]
                for msg in defaults:
                    await db_operations.save_promotion_message(msg)
        except Exception as e:
            logger.error(f"初始化默认宣传语录失败: {e}")

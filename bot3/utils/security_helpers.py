"""安全辅助函数模块

提供敏感信息保护、日志脱敏等功能。
"""

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def mask_sensitive_info(text: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """脱敏敏感信息

    Args:
        text: 原始文本
        mask_char: 掩码字符
        visible_chars: 保留可见字符数（前后各保留）

    Returns:
        脱敏后的文本
    """
    if not text or len(text) <= visible_chars * 2:
        return mask_char * len(text) if text else ""

    return (
        text[:visible_chars]
        + mask_char * (len(text) - visible_chars * 2)
        + text[-visible_chars:]
    )


def sanitize_log_message(message: str) -> str:
    """清理日志消息中的敏感信息

    自动检测并脱敏以下敏感信息：
    - Token（BOT_TOKEN等）
    - 密码
    - 用户ID（长数字）
    - 其他敏感关键词

    Args:
        message: 原始日志消息

    Returns:
        清理后的日志消息
    """
    if not message:
        return message

    # 脱敏 Token（格式：TOKEN=xxx 或 token: xxx）
    message = re.sub(
        r"(?i)(token|password|secret|key)\s*[=:]\s*([^\s,;]+)",
        lambda m: f"{m.group(1)}={mask_sensitive_info(m.group(2))}",
        message,
    )

    # 脱敏长数字（可能是用户ID或敏感数字）
    message = re.sub(
        r"\b(\d{10,})\b", lambda m: mask_sensitive_info(m.group(1)), message
    )

    return message


class SafeLogger:
    """安全日志记录器

    自动脱敏敏感信息的日志记录器包装类。
    """

    def __init__(self, logger_instance: logging.Logger):
        """
        初始化安全日志记录器

        Args:
            logger_instance: 原始日志记录器实例
        """
        self.logger = logger_instance

    def _sanitize_args(self, *args) -> tuple:
        """清理日志参数中的敏感信息"""
        return tuple(
            sanitize_log_message(str(arg)) if isinstance(arg, str) else arg
            for arg in args
        )

    def debug(self, msg: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        msg = sanitize_log_message(msg)
        args = self._sanitize_args(*args)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """记录INFO级别日志"""
        msg = sanitize_log_message(msg)
        args = self._sanitize_args(*args)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """记录WARNING级别日志"""
        msg = sanitize_log_message(msg)
        args = self._sanitize_args(*args)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """记录ERROR级别日志"""
        msg = sanitize_log_message(msg)
        args = self._sanitize_args(*args)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        msg = sanitize_log_message(msg)
        args = self._sanitize_args(*args)
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """记录异常日志"""
        msg = sanitize_log_message(msg)
        args = self._sanitize_args(*args)
        self.logger.exception(msg, *args, **kwargs)


def audit_log(
    action: str, user_id: Optional[int] = None, details: Optional[dict] = None
):
    """记录安全审计日志

    Args:
        action: 操作类型（如：login, logout, admin_action等）
        user_id: 用户ID（可选）
        details: 操作详情（可选，会自动脱敏敏感信息）
    """
    audit_logger = logging.getLogger("audit")

    # 构建审计日志消息
    log_parts = [f"[AUDIT] {action}"]

    if user_id:
        log_parts.append(f"user_id={user_id}")

    if details:
        # 脱敏详情中的敏感信息
        safe_details = {}
        for key, value in details.items():
            if isinstance(value, str) and any(
                keyword in key.lower()
                for keyword in ["token", "password", "secret", "key"]
            ):
                safe_details[key] = mask_sensitive_info(value)
            else:
                safe_details[key] = value
        log_parts.append(f"details={safe_details}")

    audit_logger.info(" | ".join(log_parts))

"""配置管理模块

支持两种配置方式：
1. Pydantic Settings（推荐）：使用 utils.config_manager
2. 传统方式（向后兼容）：环境变量 + user_config.py
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def load_config():
    """加载配置，优先从环境变量，其次从user_config.py文件（仅开发环境）"""
    # 先尝试从环境变量读取
    token = os.getenv("BOT_TOKEN")
    admin_ids_str = os.getenv("ADMIN_USER_IDS", "")

    # 检查是否为生产环境（通过 DATA_DIR 环境变量判断，或 Zeabur 环境）
    is_production = bool(os.getenv("DATA_DIR")) or bool(os.getenv("ZEABUR"))

    # 如果不是生产环境，且环境变量没有，尝试从user_config.py读取（仅用于本地开发）
    if not is_production and (not token or not admin_ids_str):
        user_config_path = Path(__file__).parent / "user_config.py"
        if user_config_path.exists():
            try:
                # 使用importlib避免循环导入
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "user_config", user_config_path
                )
                if spec is None or spec.loader is None:
                    raise ValueError("无法加载user_config模块")
                user_config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_config)

                token = token or getattr(user_config, "BOT_TOKEN", None)
                admin_ids_str = admin_ids_str or getattr(
                    user_config, "ADMIN_USER_IDS", ""
                )
            except Exception as e:
                logger.debug(f"加载user_config.py失败: {e}")

    # 验证token
    if not token:
        error_msg = "BOT_TOKEN 未设置！\n"
        if is_production:
            error_msg += "请在 Zeabur 环境变量中设置 BOT_TOKEN"
        else:
            error_msg += (
                "请选择以下方式之一设置：\n"
                "1. 设置环境变量 BOT_TOKEN\n"
                "2. 创建 user_config.py 文件，添加：BOT_TOKEN = '你的token'\n"
                "   示例：BOT_TOKEN = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'\n"
                "3. 参考 user_config.example.py 文件"
            )
        raise ValueError(error_msg)

    # 解析管理员ID
    admin_ids = []
    if admin_ids_str:
        try:
            for id_str in admin_ids_str.split(","):
                id_str = id_str.strip()
                if id_str:
                    try:
                        admin_ids.append(int(id_str))
                    except ValueError as e:
                        logger.warning(f"无法解析管理员ID '{id_str}': {e}")
        except Exception as e:
            logger.error(f"解析管理员ID列表失败: {e}", exc_info=True)

    source = "环境变量" if is_production or admin_ids_str else "user_config.py"
    logger.info(f"加载的管理员ID: {admin_ids} (来源: {source})")

    if not admin_ids:
        error_msg = "ADMIN_USER_IDS 未设置！\n"
        if is_production:
            error_msg += (
                "请在 Zeabur 环境变量中设置 ADMIN_USER_IDS（多个ID用逗号分隔，无空格）"
            )
        else:
            error_msg += (
                "请选择以下方式之一设置：\n"
                "1. 设置环境变量 ADMIN_USER_IDS（多个ID用逗号分隔）\n"
                "   示例：ADMIN_USER_IDS='123456789,987654321'\n"
                "2. 创建 user_config.py 文件，添加：ADMIN_USER_IDS = '你的用户ID1,你的用户ID2'\n"
                "   示例：ADMIN_USER_IDS = '123456789,987654321'\n"
                "3. 参考 user_config.example.py 文件"
            )
        raise ValueError(error_msg)

    return token, admin_ids


# 加载配置
# 优先使用 Pydantic Settings（如果可用），否则使用传统方式
try:
    from utils.config_manager import get_settings

    _settings = get_settings()
    BOT_TOKEN = _settings.bot_token
    ADMIN_IDS = _settings.admin_ids
    logger.info("使用 Pydantic Settings 加载配置")
except (ImportError, Exception) as e:
    # 向后兼容：使用传统方式
    logger.info(f"Pydantic Settings 不可用，使用传统配置方式: {e}")
    BOT_TOKEN, ADMIN_IDS = load_config()

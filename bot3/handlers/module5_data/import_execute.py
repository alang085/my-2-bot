"""订单导入 - 执行模块

包含执行订单导入的逻辑。
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path

from telegram import Message

logger = logging.getLogger(__name__)


async def execute_order_import(file_path: Path) -> tuple[bool, str]:
    """执行订单导入

    Args:
        file_path: Excel文件路径

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        # 导入反推函数（使用 importlib 确保在 Docker 环境中也能正常工作）
        # 确保项目根目录在路径中
        project_root = Path(__file__).parent.parent.parent.absolute()
        if os.path.exists("/app"):
            project_root = Path("/app")
        project_root = project_root.absolute()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # 尝试导入
        try:
            from reverse_orders_in_cloud import reverse_orders_from_excel_file
        except ImportError:
            # 如果导入失败，尝试直接加载模块文件
            module_path = project_root / "reverse_orders_in_cloud.py"
            if module_path.exists():
                spec = importlib.util.spec_from_file_location(
                    "reverse_orders_in_cloud", module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                reverse_orders_from_excel_file = module.reverse_orders_from_excel_file
            else:
                raise ImportError(f"无法找到模块文件: {module_path}")

        await reverse_orders_from_excel_file(str(file_path))
        return True, ""

    except Exception as e:
        logger.error(f"反推订单失败: {e}", exc_info=True)
        return False, str(e)


async def update_import_result(
    processing_msg: Message, success: bool, error_msg: str = ""
) -> None:
    """更新导入结果消息

    Args:
        processing_msg: 处理中消息对象
        success: 是否成功
        error_msg: 错误消息
    """
    if success:
        await processing_msg.edit_text(
            "✅✅✅ 订单导入完成！✅✅✅\n\n"
            "📊 所有订单已从Excel文件反推并保存到数据库\n\n"
            "💡 提示：可以使用 /report 命令查看导入结果"
        )
    else:
        await processing_msg.edit_text(
            f"❌ 订单导入失败\n\n"
            f"错误信息: {error_msg}\n\n"
            f"请检查Excel文件格式是否正确"
        )

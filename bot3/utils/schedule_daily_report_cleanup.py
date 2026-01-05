"""每日报表 - 清理模块

包含清理临时文件的逻辑。
"""

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


def cleanup_temp_files(file_paths: List[Optional[str]]) -> None:
    """清理临时文件

    Args:
        file_paths: 文件路径列表
    """
    for file_path in file_paths:
        if file_path:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败 {file_path}: {e}")

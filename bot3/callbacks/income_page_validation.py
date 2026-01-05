"""收入明细分页 - 验证模块

包含验证管理员权限的逻辑。
"""

from config import ADMIN_IDS


async def validate_admin_access(query, user_id: int) -> bool:
    """验证管理员访问权限

    Args:
        query: 回调查询对象
        user_id: 用户ID

    Returns:
        bool: 是否有权限
    """
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return False
    return True

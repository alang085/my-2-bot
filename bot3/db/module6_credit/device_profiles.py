"""手机档案数据库操作"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

from db.base import execute_query, execute_transaction

logger = logging.getLogger(__name__)


def _generate_device_id(
    imei: Optional[str] = None, device_info: Optional[dict] = None
) -> str:
    """生成设备ID"""
    if imei:
        return f"DEV_{imei}"
    if device_info:
        device_str = json.dumps(device_info, sort_keys=True)
        device_hash = hashlib.sha256(device_str.encode()).hexdigest()[:12]
        return f"DEV_{device_hash}"
    return f"DEV_{datetime.now().strftime('%Y%m%d%H%M%S')}"


async def create_device_profile(
    imei: Optional[str] = None,
    device_model: Optional[str] = None,
    os_version: Optional[str] = None,
    app_version: Optional[str] = None,
    device_info: Optional[dict] = None,
    customer_id: Optional[str] = None,
) -> str:
    """创建设备档案，返回设备ID"""
    device_id = _generate_device_id(imei, device_info)
    first_seen_date = datetime.now().strftime("%Y-%m-%d")
    device_info_json = json.dumps(device_info) if device_info else None

    query = """
        INSERT INTO device_profiles (
            device_id, customer_id, imei, device_model, os_version,
            app_version, device_info, first_seen_date, last_seen_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        device_id,
        customer_id,
        imei,
        device_model,
        os_version,
        app_version,
        device_info_json,
        first_seen_date,
        first_seen_date,
    )
    if await execute_transaction(query, params):
        return device_id
    return ""


async def get_device_by_id(device_id: str) -> Optional[dict]:
    """根据设备ID获取设备档案"""
    result = await execute_query(
        "SELECT * FROM device_profiles WHERE device_id = ? LIMIT 1",
        (device_id,),
        fetch_one=True,
    )
    if result and isinstance(result, dict) and result.get("device_info"):
        try:
            result["device_info"] = json.loads(result["device_info"])
        except (json.JSONDecodeError, TypeError):
            pass
    return result if isinstance(result, dict) else None


async def get_device_by_imei(imei: str) -> Optional[dict]:
    """根据IMEI获取设备档案"""
    result = await execute_query(
        "SELECT * FROM device_profiles WHERE imei = ? LIMIT 1", (imei,), fetch_one=True
    )
    if result and isinstance(result, dict) and result.get("device_info"):
        try:
            result["device_info"] = json.loads(result["device_info"])
        except (json.JSONDecodeError, TypeError):
            pass
    return result if isinstance(result, dict) else None


async def link_device_to_customer(device_id: str, customer_id: str) -> bool:
    """关联设备和客户"""
    query = """
        UPDATE device_profiles 
        SET customer_id = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE device_id = ?
    """
    return await execute_transaction(query, (customer_id, device_id))


async def set_device_blacklist(device_id: str, is_blacklisted: bool) -> bool:
    """设置设备黑名单状态"""
    query = """
        UPDATE device_profiles 
        SET is_blacklisted = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE device_id = ?
    """
    return await execute_transaction(query, (1 if is_blacklisted else 0, device_id))


async def set_device_whitelist(device_id: str, is_whitelisted: bool) -> bool:
    """设置设备白名单状态"""
    query = """
        UPDATE device_profiles 
        SET is_whitelisted = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE device_id = ?
    """
    return await execute_transaction(query, (1 if is_whitelisted else 0, device_id))


async def is_device_blacklisted(device_id: str) -> bool:
    """检查设备是否在黑名单"""
    result = await execute_query(
        "SELECT is_blacklisted FROM device_profiles WHERE device_id = ? LIMIT 1",
        (device_id,),
        fetch_one=True,
    )
    if result and isinstance(result, dict):
        return result.get("is_blacklisted", 0) == 1
    return False


async def is_device_whitelisted(device_id: str) -> bool:
    """检查设备是否在白名单"""
    result = await execute_query(
        "SELECT is_whitelisted FROM device_profiles WHERE device_id = ? LIMIT 1",
        (device_id,),
        fetch_one=True,
    )
    if result and isinstance(result, dict):
        return result.get("is_whitelisted", 0) == 1
    return False

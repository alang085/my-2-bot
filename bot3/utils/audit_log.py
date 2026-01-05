"""审计日志系统

提供操作审计日志记录和查询功能。
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 审计日志存储
_audit_logs: deque = deque(maxlen=10000)
_audit_lock = asyncio.Lock()


async def log_audit_event(
    event_type: str,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """记录审计事件

    Args:
        event_type: 事件类型
        user_id: 用户ID（可选）
        action: 操作名称（可选）
        resource: 资源名称（可选）
        details: 事件详情（可选）
        ip_address: IP地址（可选）

    Returns:
        审计日志记录
    """
    audit_record = {
        "event_type": event_type,
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details or {},
        "ip_address": ip_address,
        "timestamp": datetime.now().isoformat(),
    }

    async with _audit_lock:
        _audit_logs.append(audit_record)

    logger.info(f"审计日志: {event_type} - User: {user_id} - Action: {action}")

    return audit_record


async def get_audit_logs(
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """获取审计日志

    Args:
        user_id: 用户ID过滤（可选）
        event_type: 事件类型过滤（可选）
        start_time: 开始时间过滤（可选）
        end_time: 结束时间过滤（可选）
        limit: 最大返回数量

    Returns:
        审计日志列表
    """
    async with _audit_lock:
        logs = list(_audit_logs)

    # 应用过滤
    if user_id:
        logs = [log for log in logs if log.get("user_id") == user_id]
    if event_type:
        logs = [log for log in logs if log.get("event_type") == event_type]
    if start_time:
        logs = [
            log
            for log in logs
            if datetime.fromisoformat(log["timestamp"]) >= start_time
        ]
    if end_time:
        logs = [
            log for log in logs if datetime.fromisoformat(log["timestamp"]) <= end_time
        ]

    # 返回最近的日志
    return logs[-limit:]


async def get_audit_summary(hours: int = 24) -> Dict[str, Any]:
    """获取审计摘要

    Args:
        hours: 时间范围（小时）

    Returns:
        审计摘要字典
    """
    async with _audit_lock:
        logs = list(_audit_logs)

    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_logs = [
        log for log in logs if datetime.fromisoformat(log["timestamp"]) >= cutoff_time
    ]

    summary: dict[str, Any] = {
        "total_events": len(recent_logs),
        "by_event_type": {},
        "by_user": {},
        "by_action": {},
    }

    for log in recent_logs:
        # 按事件类型统计
        event_type = log.get("event_type", "unknown")
        if isinstance(summary["by_event_type"], dict):
            summary["by_event_type"][event_type] = (
                summary["by_event_type"].get(event_type, 0) + 1
            )

        # 按用户统计
        user_id = log.get("user_id")
        if user_id and isinstance(summary["by_user"], dict):
            summary["by_user"][user_id] = summary["by_user"].get(user_id, 0) + 1

        # 按操作统计
        action = log.get("action", "unknown")
        if isinstance(summary["by_action"], dict):
            summary["by_action"][action] = summary["by_action"].get(action, 0) + 1

    return summary


async def export_audit_logs(format: str = "json") -> str:
    """导出审计日志

    Args:
        format: 导出格式（json/csv）

    Returns:
        导出的日志字符串
    """
    async with _audit_lock:
        logs = list(_audit_logs)

    if format == "json":
        import json

        return json.dumps(logs, indent=2, ensure_ascii=False)
    elif format == "csv":
        import csv
        from io import StringIO

        output = StringIO()
        if logs:
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)
        return output.getvalue()
    else:
        raise ValueError(f"不支持的格式: {format}")

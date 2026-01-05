"""消息构建器类模块

提供统一的消息构建方法，简化重复的消息格式化代码。
"""

from typing import Dict, List, Optional, Tuple, Union

from constants import TELEGRAM_MESSAGE_SAFE_LENGTH


class MessageBuilder:
    """消息构建器类，提供统一的消息格式化方法"""

    @staticmethod
    def build_success_message(
        action: str,
        details: Optional[Dict] = None,
        is_group: bool = False,
    ) -> str:
        """构建成功消息

        Args:
            action: 操作名称（如 "Order Created", "Status Updated"）
            details: 详细信息字典，可包含 order_id, amount, state 等
            is_group: 是否为群聊（群聊使用简短消息，私聊使用详细消息）

        Returns:
            格式化后的成功消息
        """
        if is_group:
            if details and "order_id" in details:
                return f"✅ {action}\nOrder ID: {details['order_id']}"
            return f"✅ {action}"
        else:
            message = f"✅ {action}"
            if details:
                if "order_id" in details:
                    message += f"\nOrder ID: {details['order_id']}"
                if "amount" in details:
                    message += f"\nAmount: {details['amount']:.2f}"
                if "state" in details:
                    message += f"\nState: {details['state']}"
            return message

    @staticmethod
    def build_error_message(
        error: str,
        details: Optional[Dict] = None,
        is_group: bool = False,
    ) -> str:
        """构建错误消息

        Args:
            error: 错误描述
            details: 详细信息字典
            is_group: 是否为群聊

        Returns:
            格式化后的错误消息
        """
        if is_group:
            return f"❌ {error}"
        else:
            message = f"❌ {error}"
            if details:
                if "order_id" in details:
                    message += f"\nOrder ID: {details['order_id']}"
                if "amount" in details:
                    message += f"\nAmount: {details['amount']:.2f}"
            return message

    @staticmethod
    def build_warning_message(
        warning: str,
        details: Optional[Dict] = None,
        is_group: bool = False,
    ) -> str:
        """构建警告消息

        Args:
            warning: 警告描述
            details: 详细信息字典
            is_group: 是否为群聊

        Returns:
            格式化后的警告消息
        """
        if is_group:
            return f"⚠️ {warning}"
        else:
            message = f"⚠️ {warning}"
            if details:
                if "order_id" in details:
                    message += f"\nOrder ID: {details['order_id']}"
            return message

    @staticmethod
    def build_info_message(
        title: str,
        items: Optional[List[Dict[str, Union[str, float, int]]]] = None,
        footer: Optional[str] = None,
    ) -> str:
        """构建信息消息（带列表项）

        Args:
            title: 消息标题
            items: 信息项列表，每个项是 {"label": "...", "value": ...} 格式
            footer: 底部信息

        Returns:
            格式化后的信息消息
        """
        message = f"{title}\n"
        if items:
            message += "\n"
            for item in items:
                label = item.get("label", "")
                value = item.get("value", "")
                if isinstance(value, float):
                    value_str = f"{value:.2f}"
                elif isinstance(value, int):
                    value_str = str(value)
                else:
                    value_str = str(value)
                message += f"{label}: {value_str}\n"
        if footer:
            message += f"\n{footer}"
        return message

    @staticmethod
    def build_table_message(
        title: str,
        headers: List[str],
        rows: List[List[Union[str, float, int]]],
        footer: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> str:
        """构建表格消息

        Args:
            title: 表格标题
            headers: 表头列表
            rows: 数据行列表，每行是一个列表
            footer: 底部信息
            max_rows: 最大显示行数，如果为None则显示所有行

        Returns:
            格式化后的表格消息
        """
        message = f"{title}\n\n"

        col_widths = [len(str(h)) for h in headers]
        for row in rows[:max_rows] if max_rows else rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        header_row = " | ".join(
            str(h).ljust(col_widths[i]) for i, h in enumerate(headers)
        )
        message += header_row + "\n"
        message += "-" * len(header_row) + "\n"

        display_rows = rows[:max_rows] if max_rows else rows
        for row in display_rows:
            row_str = " | ".join(
                str(cell).ljust(col_widths[i]) if i < len(col_widths) else str(cell)
                for i, cell in enumerate(row)
            )
            message += row_str + "\n"

        if max_rows and len(rows) > max_rows:
            message += f"\n... 还有 {len(rows) - max_rows} 行未显示"

        if footer:
            message += f"\n{footer}"

        return message

    @staticmethod
    def build_list_message(
        title: str,
        items: List[Union[str, Dict[str, Union[str, float, int]]]],
        footer: Optional[str] = None,
        max_items: Optional[int] = None,
        item_format: Optional[str] = None,
    ) -> str:
        """构建列表消息

        Args:
            title: 列表标题
            items: 列表项，可以是字符串列表或字典列表
            footer: 底部信息
            max_items: 最大显示项数，如果为None则显示所有项
            item_format: 项格式字符串，如 "{index}. {item}"，如果为None则使用默认格式

        Returns:
            格式化后的列表消息
        """
        message = f"{title}\n\n"

        display_items = items[:max_items] if max_items else items

        for i, item in enumerate(display_items, 1):
            if isinstance(item, dict):
                item_str = ", ".join(f"{k}: {v}" for k, v in item.items())
            else:
                item_str = str(item)

            if item_format:
                message += item_format.format(index=i, item=item_str) + "\n"
            else:
                message += f"{i}. {item_str}\n"

        if max_items and len(items) > max_items:
            message += f"\n... 还有 {len(items) - max_items} 项未显示"

        if footer:
            message += f"\n{footer}"

        return message

    @staticmethod
    def build_paginated_message(
        title: str,
        items: List[str],
        page: int = 1,
        items_per_page: int = 10,
        footer: Optional[str] = None,
    ) -> Tuple[str, bool, bool]:
        """构建分页消息

        Args:
            title: 消息标题
            items: 所有项目列表
            page: 当前页码（从1开始）
            items_per_page: 每页显示项数
            footer: 底部信息

        Returns:
            Tuple[message, has_prev, has_next]:
                - message: 格式化后的消息
                - has_prev: 是否有上一页
                - has_next: 是否有下一页
        """
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]

        message = f"{title}\n\n"
        for i, item in enumerate(page_items, start_idx + 1):
            message += f"{i}. {item}\n"

        if footer:
            message += f"\n{footer}"

        message += f"\n\n📄 第 {page}/{total_pages} 页 (共 {len(items)} 项)"

        has_prev = page > 1
        has_next = page < total_pages

        return message, has_prev, has_next

    @staticmethod
    def _split_long_line(line: str, max_length: int) -> List[str]:
        """分割超长行

        Args:
            line: 要分割的行
            max_length: 最大长度

        Returns:
            分割后的行列表
        """
        words = line.split()
        result = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 > max_length:
                if current_line:
                    result.append(current_line.strip())
                current_line = word
            else:
                current_line += (" " if current_line else "") + word

        if current_line:
            result.append(current_line.strip())

        return result

    @staticmethod
    def _process_long_line(
        line: str, current_message: str, max_length: int, messages: List[str]
    ) -> str:
        """处理超长行

        Args:
            line: 当前行
            current_message: 当前消息
            max_length: 最大长度
            messages: 消息列表

        Returns:
            更新后的当前消息
        """
        if current_message:
            messages.append(current_message.strip())
            current_message = ""

        split_lines = MessageBuilder._split_long_line(line, max_length)
        if split_lines:
            messages.extend(split_lines[:-1])
            current_message = split_lines[-1]

        return current_message

    @staticmethod
    def _process_normal_line(
        line: str, current_message: str, max_length: int, messages: List[str]
    ) -> str:
        """处理普通行

        Args:
            line: 当前行
            current_message: 当前消息
            max_length: 最大长度
            messages: 消息列表

        Returns:
            更新后的当前消息
        """
        test_message = current_message + ("\n" if current_message else "") + line
        if len(test_message) > max_length:
            if current_message:
                messages.append(current_message.strip())
            current_message = line
        else:
            current_message = test_message

        return current_message

    def split_long_message(
        message: str, max_length: int = TELEGRAM_MESSAGE_SAFE_LENGTH
    ) -> List[str]:
        """分割长消息为多个消息

        Args:
            message: 原始消息
            max_length: 每条消息的最大长度

        Returns:
            消息列表
        """
        if len(message) <= max_length:
            return [message]

        messages = []
        lines = message.split("\n")
        current_message = ""

        for line in lines:
            if len(line) > max_length:
                current_message = MessageBuilder._process_long_line(
                    line, current_message, max_length, messages
                )
            else:
                current_message = MessageBuilder._process_normal_line(
                    line, current_message, max_length, messages
                )

        if current_message:
            messages.append(current_message.strip())

        return messages

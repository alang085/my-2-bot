"""通用查询构建器

提供统一的数据库查询构建方法，简化重复的查询代码。
"""

from typing import Dict, List, Optional, Tuple, Union


class QueryBuilder:
    """查询构建器类，提供统一的查询构建方法"""

    def __init__(self, table: str):
        """初始化查询构建器

        Args:
            table: 表名
        """
        self.table = table
        self.select_fields = ["*"]
        self.where_conditions: List[str] = []
        self.where_params: List[Union[str, int, float, None]] = []
        self.order_by: Optional[str] = None
        self.limit_value: Optional[int] = None
        self.offset_value: Optional[int] = None

    def select(self, fields: Union[str, List[str]]) -> "QueryBuilder":
        """设置要查询的字段

        Args:
            fields: 字段名或字段列表，如 "*" 或 ["id", "name", "amount"]

        Returns:
            self，支持链式调用
        """
        if isinstance(fields, str):
            self.select_fields = [fields]
        else:
            self.select_fields = fields
        return self

    def where(
        self, condition: str, value: Optional[Union[str, int, float]] = None
    ) -> "QueryBuilder":
        """添加 WHERE 条件

        Args:
            condition: WHERE 条件，如 "field = ?" 或 "field IS NULL"
            value: 条件值（如果条件包含 ?）

        Returns:
            self，支持链式调用

        Example:
            builder.where("id = ?", 123)
            builder.where("status IS NOT NULL")
        """
        self.where_conditions.append(condition)
        if value is not None:
            self.where_params.append(value)
        return self

    def where_in(self, field: str, values: List[Union[str, int]]) -> "QueryBuilder":
        """添加 WHERE field IN (?, ?, ...) 条件

        Args:
            field: 字段名
            values: 值列表

        Returns:
            self，支持链式调用
        """
        if not values:
            return self
        placeholders = ",".join(["?"] * len(values))
        self.where_conditions.append(f"{field} IN ({placeholders})")
        self.where_params.extend(values)
        return self

    def where_not_in(self, field: str, values: List[Union[str, int]]) -> "QueryBuilder":
        """添加 WHERE field NOT IN (?, ?, ...) 条件

        Args:
            field: 字段名
            values: 值列表

        Returns:
            self，支持链式调用
        """
        if not values:
            return self
        placeholders = ",".join(["?"] * len(values))
        self.where_conditions.append(f"{field} NOT IN ({placeholders})")
        self.where_params.extend(values)
        return self

    def order_by_field(self, field: str, direction: str = "ASC") -> "QueryBuilder":
        """设置排序

        Args:
            field: 排序字段
            direction: 排序方向，ASC 或 DESC

        Returns:
            self，支持链式调用
        """
        self.order_by = f"{field} {direction.upper()}"
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """设置 LIMIT

        Args:
            count: 限制数量

        Returns:
            self，支持链式调用
        """
        self.limit_value = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """设置 OFFSET

        Args:
            count: 偏移量

        Returns:
            self，支持链式调用
        """
        self.offset_value = count
        return self

    def build(self) -> Tuple[str, List[Union[str, int, float, None]]]:
        """构建查询语句和参数

        Returns:
            Tuple[query_string, params]: 查询语句和参数列表
        """
        # 构建 SELECT 部分
        fields_str = ", ".join(self.select_fields)
        query = f"SELECT {fields_str} FROM {self.table}"

        # 构建 WHERE 部分
        if self.where_conditions:
            query += " WHERE " + " AND ".join(self.where_conditions)

        # 构建 ORDER BY 部分
        if self.order_by:
            query += f" ORDER BY {self.order_by}"

        # 构建 LIMIT 部分
        if self.limit_value is not None:
            query += f" LIMIT {self.limit_value}"

        # 构建 OFFSET 部分
        if self.offset_value is not None:
            query += f" OFFSET {self.offset_value}"

        return query, self.where_params

    def reset(self) -> "QueryBuilder":
        """重置构建器状态

        Returns:
            self，支持链式调用
        """
        self.select_fields = ["*"]
        self.where_conditions = []
        self.where_params = []
        self.order_by = None
        self.limit_value = None
        self.offset_value = None
        return self


class UpdateBuilder:
    """UPDATE 查询构建器"""

    def __init__(self, table: str):
        """初始化 UPDATE 构建器

        Args:
            table: 表名
        """
        self.table = table
        self.set_fields: List[str] = []
        self.set_params: List[Union[str, int, float, None]] = []
        self.where_conditions: List[str] = []
        self.where_params: List[Union[str, int, float, None]] = []

    def set(
        self, field: str, value: Optional[Union[str, int, float]]
    ) -> "UpdateBuilder":
        """设置要更新的字段

        Args:
            field: 字段名
            value: 字段值

        Returns:
            self，支持链式调用
        """
        self.set_fields.append(f"{field} = ?")
        self.set_params.append(value)
        return self

    def where(
        self, condition: str, value: Optional[Union[str, int, float]] = None
    ) -> "UpdateBuilder":
        """添加 WHERE 条件

        Args:
            condition: WHERE 条件
            value: 条件值（如果条件包含 ?）

        Returns:
            self，支持链式调用
        """
        self.where_conditions.append(condition)
        if value is not None:
            self.where_params.append(value)
        return self

    def build(self) -> Tuple[str, List[Union[str, int, float, None]]]:
        """构建 UPDATE 语句和参数

        Returns:
            Tuple[query_string, params]: 查询语句和参数列表（SET 参数在前，WHERE 参数在后）
        """
        if not self.set_fields:
            raise ValueError("UPDATE 语句必须至少设置一个字段")

        query = f"UPDATE {self.table} SET {', '.join(self.set_fields)}"

        if self.where_conditions:
            query += " WHERE " + " AND ".join(self.where_conditions)

        # 参数顺序：SET 参数在前，WHERE 参数在后
        params = self.set_params + self.where_params

        return query, params

    def reset(self) -> "UpdateBuilder":
        """重置构建器状态

        Returns:
            self，支持链式调用
        """
        self.set_fields = []
        self.set_params = []
        self.where_conditions = []
        self.where_params = []
        return self


# 便捷函数
def _apply_filters_to_builder(
    builder: QueryBuilder,
    filters: Optional[Dict[str, Union[str, int, float, List[Union[str, int]]]]],
) -> None:
    """应用过滤条件到查询构建器

    Args:
        builder: 查询构建器
        filters: 过滤条件字典
    """
    if not filters:
        return

    for field, value in filters.items():
        if isinstance(value, list):
            builder.where_in(field, value)
        elif value is None:
            builder.where(f"{field} IS NULL")
        else:
            builder.where(f"{field} = ?", value)


def _apply_order_by_to_builder(builder: QueryBuilder, order_by: Optional[str]) -> None:
    """应用排序到查询构建器

    Args:
        builder: 查询构建器
        order_by: 排序字段，如 "created_at DESC"
    """
    if not order_by:
        return

    parts = order_by.split()
    if len(parts) == 2:
        builder.order_by_field(parts[0], parts[1])
    else:
        builder.order_by_field(parts[0])


def _apply_limit_and_offset(
    builder: QueryBuilder, limit: Optional[int], offset: Optional[int]
) -> None:
    """应用限制和偏移到查询构建器

    Args:
        builder: 查询构建器
        limit: 限制数量
        offset: 偏移量
    """
    if limit is not None:
        builder.limit(limit)

    if offset is not None:
        builder.offset(offset)


def build_select_query(
    table: str,
    filters: Optional[Dict[str, Union[str, int, float, List[Union[str, int]]]]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[str, List[Union[str, int, float, None]]]:
    """快速构建 SELECT 查询

    Args:
        table: 表名
        filters: 过滤条件字典，如 {"id": 123, "status": "active"}
        order_by: 排序字段，如 "created_at DESC"
        limit: 限制数量
        offset: 偏移量

    Returns:
        Tuple[query_string, params]

    Example:
        query, params = build_select_query(
            "orders",
            filters={"state": "normal", "group_id": "S01"},
            order_by="created_at DESC",
            limit=10
        )
    """
    builder = QueryBuilder(table)
    _apply_filters_to_builder(builder, filters)
    _apply_order_by_to_builder(builder, order_by)
    _apply_limit_and_offset(builder, limit, offset)
    return builder.build()


def build_update_query(
    table: str,
    updates: Dict[str, Union[str, int, float, None]],
    filters: Optional[Dict[str, Union[str, int, float]]] = None,
) -> Tuple[str, List[Union[str, int, float, None]]]:
    """快速构建 UPDATE 查询

    Args:
        table: 表名
        updates: 要更新的字段字典，如 {"status": "active", "amount": 1000}
        filters: WHERE 条件字典

    Returns:
        Tuple[query_string, params]

    Example:
        query, params = build_update_query(
            "orders",
            updates={"state": "normal", "amount": 5000},
            filters={"chat_id": 123456}
        )
    """
    builder = UpdateBuilder(table)

    for field, value in updates.items():
        builder.set(field, value)

    if filters:
        for field, value in filters.items():
            if value is None:
                builder.where(f"{field} IS NULL")
            else:
                builder.where(f"{field} = ?", value)

    return builder.build()

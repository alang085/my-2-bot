"""常量定义"""

# 星期分组映射
WEEKDAY_GROUP = {
    0: "一",  # Monday
    1: "二",  # Tuesday
    2: "三",  # Wednesday
    3: "四",  # Thursday
    4: "五",  # Friday
    5: "六",  # Saturday
    6: "日",  # Sunday
}

# 订单状态
ORDER_STATES = {
    "normal": "正常",
    "overdue": "逾期",
    "breach": "违约",
    "end": "完成",
    "breach_end": "违约完成",
}

# 历史订单阈值日期（2025-11-28之前的订单不扣款，不播报）
HISTORICAL_THRESHOLD_DATE = (2025, 11, 28)

# 日结时间阈值（23:00）
DAILY_CUTOFF_HOUR = 23

# 允许的日结字段前缀
DAILY_ALLOWED_PREFIXES = [
    "new_clients",
    "old_clients",
    "interest",
    "completed",
    "breach",
    "breach_end",
]

# 收入类型
INCOME_TYPES = {
    "completed": "订单完成",
    "breach_end": "违约完成",
    "interest": "利息收入",
    "principal_reduction": "本金减少",
    "adjustment": "资金调整",
}

# 客户类型
CUSTOMER_TYPES = {"A": "新客户", "B": "老客户", None: "无关联"}

# 用户状态
USER_STATES = {
    "WAITING_BREACH_END_AMOUNT": "等待违约完成金额",
    "SEARCHING": "搜索中",
    "REPORT_QUERY": "报表查询",
    "QUERY_EXPENSE_COMPANY": "查询公司开销",
    "QUERY_EXPENSE_OTHER": "查询其他开销",
    "WAITING_EXPENSE_COMPANY": "等待公司开销输入",
    "WAITING_EXPENSE_OTHER": "等待其他开销输入",
    "BROADCAST_PAYMENT": "播报付款提醒",
    "REPORT_SEARCHING": "报表查找中",
    "UPDATING_BALANCE_GCASH": "更新GCASH余额",
    "UPDATING_BALANCE_PAYMAYA": "更新PayMaya余额",
    "EDITING_ACCOUNT_GCASH": "编辑GCASH账号",
    "EDITING_ACCOUNT_PAYMAYA": "编辑PayMaya账号",
    "ADDING_ACCOUNT_GCASH": "添加GCASH账户",
    "ADDING_ACCOUNT_PAYMAYA": "添加PayMaya账户",
    "EDITING_ACCOUNT_BY_ID_GCASH": "编辑GCASH账户（按ID）",
    "EDITING_ACCOUNT_BY_ID_PAYMAYA": "编辑PayMaya账户（按ID）",
    "SEARCHING_AMOUNT": "搜索中（按金额）",
    "QUERY_INCOME": "查询收入明细",
    "SETTING_GROUP_LINKS": "设置群组链接",
    "SETTING_BOT_LINKS": "设置机器人链接",
    "SETTING_WORKER_LINKS": "设置人工链接",
}

# Telegram 消息长度限制
TELEGRAM_MESSAGE_MAX_LENGTH = 4096  # Telegram 消息最大长度
TELEGRAM_MESSAGE_SAFE_LENGTH = 4000  # 安全的消息长度（留出余量）

# 显示限制
MAX_DISPLAY_ITEMS = 10  # 默认最大显示项目数
MAX_DISPLAY_ITEMS_LARGE = 20  # 大型列表的最大显示项目数
MAX_DISPLAY_ITEMS_SMALL = 3  # 小型列表的最大显示项目数

# 字符串截断长度
MAX_NOTE_LENGTH = 30  # 备注最大显示长度
MAX_ACCOUNT_NAME_LENGTH = 20  # 账户名称最大显示长度

# 金额和百分比
PRINCIPAL_PERCENTAGE = 0.12  # 本金百分比（12%）
AMOUNT_TOLERANCE = 0.01  # 金额容差（用于浮点数比较）
AMOUNT_THOUSAND = 1000  # 金额单位（千）

# 日期相关
DATE_FORMAT = "%Y-%m-%d"  # 日期格式
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # 日期时间格式
DATE_EXAMPLE = "2025-01-15"  # 日期示例

# 订单创建日期阈值（2025-12-26）
ORDER_CREATE_CUTOFF_DATE = (
    2025,
    12,
    26,
)  # 此日期之后的订单创建新订单，之前的更新现有订单

# 默认值
DEFAULT_GROUP_ID = "S01"  # 默认归属ID
DEFAULT_ANNOUNCEMENT_INTERVAL = 3  # 默认公告间隔（小时）
DEFAULT_WEEKDAYS = 7  # 一周的天数

# 错误消息模板
ERROR_MESSAGES = {
    "DATE_FORMAT_ERROR": "❌ 日期格式错误",
    "DATE_FORMAT_USAGE": "正确格式: YYYY-MM-DD\n例如: 2025-01-15",
    "USAGE_ERROR": "❌ 用法错误",
    "PERMISSION_DENIED": "❌ 权限不足",
    "ADMIN_REQUIRED": "⚠️ 此操作需要管理员权限",
    "AUTHORIZED_REQUIRED": "⚠️ 此操作需要授权用户权限",
    "OPERATION_FAILED": "❌ 操作失败",
    "INVALID_INPUT": "❌ 输入无效",
    "NOT_FOUND": "❌ 未找到",
}

# 输入验证错误消息
VALIDATION_ERRORS = {
    "invalid_integer": "❌ 请输入有效的整数",
    "invalid_float": "❌ 请输入有效的数字",
    "invalid_amount": "❌ 请输入有效的金额",
    "amount_too_small": "❌ 金额必须大于 {min_amount}",
    "amount_too_large": "❌ 金额不能超过 {max_amount:,.2f}",
    "invalid_date_format": "❌ 日期格式错误，请使用格式：{format}（例如：{example}）",
    "invalid_order_id": "❌ 订单ID必须是4位数字（例如：0001, 0123）",
    "invalid_group_id": "❌ 归属ID格式错误，应为1个字母+2位数字（例如：S01, A12）",
    "invalid_customer_type": "❌ 客户类型必须是 A（新客户）或 B（老客户）",
    "invalid_order_state": "❌ 订单状态无效，有效状态：{valid_states}",
    "text_too_long": "❌ {field_name}长度不能超过 {max_length} 个字符",
    "text_empty": "❌ {field_name}不能为空",
    "invalid_time_format": "❌ 时间格式错误，请输入小时（0-23）或小时:分钟（如 22:30）",
    "invalid_chat_id": "❌ 聊天ID必须是有效的数字",
    "value_out_of_range": "❌ 数值必须在 {min_value} 到 {max_value} 之间",
    "value_too_small": "❌ 数值必须大于等于 {min_value}",
    "value_too_large": "❌ 数值必须小于等于 {max_value}",
}

# 状态相关错误消息
STATE_ERRORS = {
    "state_not_found": "❌ 未找到用户状态",
    "state_invalid": "❌ 用户状态无效",
    "state_expired": "❌ 操作已超时，请重新开始",
    "state_cleared": "✅ 状态已清除",
}

# 权限相关错误消息
PERMISSION_ERRORS = {
    "admin_required": "❌ 此操作需要管理员权限",
    "authorized_required": "❌ 此操作需要授权用户权限",
    "private_chat_only": "❌ 此命令只能在私聊中使用",
    "group_chat_only": "❌ 此命令只能在群组中使用",
}

# 数据库相关错误消息
DATABASE_ERRORS = {
    "connection_failed": "❌ 数据库连接失败",
    "query_failed": "❌ 数据库查询失败",
    "update_failed": "❌ 数据库更新失败",
    "record_not_found": "❌ 记录不存在",
    "duplicate_record": "❌ 记录已存在",
}

# 成功消息模板
SUCCESS_MESSAGES = {
    "OPERATION_SUCCESS": "✅ 操作成功",
    "UPDATE_SUCCESS": "✅ 更新成功",
    "CREATE_SUCCESS": "✅ 创建成功",
    "DELETE_SUCCESS": "✅ 删除成功",
}

# API 文档

## 数据库操作层 API (`db/`)

### 模块2：财务管理 (`db/module2_finance/`)

#### `finance.py` - 财务数据操作

##### `get_financial_data(conn, cursor) -> Dict`
获取全局财务数据。

**返回**: 包含财务数据的字典，如果不存在则返回默认值。

##### `update_financial_data(conn, cursor, field: str, amount: float) -> bool`
更新财务数据字段。

**参数**:
- `field`: 要更新的字段名
- `amount`: 要增加/减少的金额（正数表示增加，负数表示减少）

**返回**: 如果成功更新，返回 True；否则返回 False

##### `get_grouped_data(conn, cursor, group_id: Optional[str] = None) -> Dict`
获取分组数据。

**参数**:
- `group_id`: 归属ID，如果为 None 则获取所有分组数据

**返回**: 分组数据字典

##### `update_grouped_data(conn, cursor, group_id: str, field: str, amount: float) -> bool`
更新分组数据字段。

**参数**:
- `group_id`: 归属ID
- `field`: 要更新的字段名
- `amount`: 要增加/减少的金额

**返回**: 如果成功更新，返回 True；否则返回 False

#### `income_basic.py` - 收入记录操作

##### `record_income(...) -> Optional[int]`
记录收入。

**参数**: 见函数定义

**返回**: 收入记录ID，如果失败则返回 None

##### `get_income_records(start_date: str, end_date: str, type: Optional[str] = None) -> List[Dict]`
获取收入记录。

**参数**:
- `start_date`: 开始日期
- `end_date`: 结束日期
- `type`: 收入类型（可选）

**返回**: 收入记录列表

### 模块3：订单管理 (`db/module3_order/`)

#### `orders_basic.py` - 订单基础操作

##### `create_order(...) -> Tuple[bool, Optional[str]]`
创建订单。

**返回**: (是否成功, 订单ID或错误消息)

##### `create_order_in_classified_tables(...) -> bool`
在分类表中创建订单。

**返回**: 是否成功

## 服务层 API (`services/`)

### 模块3：订单管理 (`services/module3_order/`)

#### `order_service.py` - 订单服务

##### `OrderService._validate_and_update_state(chat_id: int, new_state: str, allowed_old_states: Tuple[str, ...]) -> Tuple[bool, Optional[str], ...]`
验证订单并更新状态。

**参数**:
- `chat_id`: 群组ID
- `new_state`: 新状态
- `allowed_old_states`: 允许的旧状态列表

**返回**: (success, error_msg, order_model, old_state, group_id, amount)

## 工具层 API (`utils/`)

### 订单创建 (`utils/order_creation_*.py`)

#### `order_creation_main.py`

##### `try_create_order_from_title(update, context, chat, title: str, manual_trigger: bool = False, allow_create_new: bool = True)`
尝试从群标题创建订单。

**参数**:
- `update`: Telegram 更新对象
- `context`: 上下文对象
- `chat`: 聊天对象
- `title`: 群名
- `manual_trigger`: 是否手动触发
- `allow_create_new`: 是否允许创建新订单

#### `order_creation_execute.py`

##### `execute_order_creation_flow(params: OrderCreationParams) -> bool`
执行订单创建流程。

**参数**:
- `params`: 订单创建参数

**返回**: 是否成功创建

## 注意事项

1. 所有数据库操作函数都使用装饰器 `@db_query` 或 `@db_transaction`
2. 异步函数需要使用 `await` 调用
3. 函数参数中的 `conn` 和 `cursor` 由装饰器自动注入

## 向后兼容

所有函数都可以通过 `db_operations` 模块访问，保持向后兼容。


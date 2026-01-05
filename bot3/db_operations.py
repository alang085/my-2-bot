"""
数据库操作模块（统一入口 - 向后兼容层）

此文件作为向后兼容的统一入口，导入所有拆分后的数据库操作模块。

所有函数都从以下模块导入：
- db.module1_user.users - 用户权限操作
- db.module2_finance.finance - 财务数据操作
- db.module2_finance.income - 收入明细操作
- db.module2_finance.payments - 支付账号操作
- db.module2_finance.daily - 日结数据操作
- db.module3_order.orders - 订单操作
- db.module4_automation.messages - 消息配置操作
- db.module5_data.reports - 报表操作
- db.module5_data.history - 操作历史

注意：
    - 此文件保持向后兼容，所有现有代码无需修改
    - 新代码应该直接从 db.moduleX_xxx 模块导入
"""

# 模块1：用户权限管理
from db.module1_user.users import add_authorized_user  # noqa: F401, F403
from db.module1_user.users import (get_all_user_group_mappings,
                                   get_authorized_users, get_user_group_id,
                                   is_user_authorized, remove_authorized_user,
                                   remove_user_group_id, set_user_group_id)
# 模块2：财务管理
from db.module2_finance.daily import *  # noqa: F401, F403
from db.module2_finance.finance import *  # noqa: F401, F403
from db.module2_finance.income import *  # noqa: F401, F403
from db.module2_finance.payments import *  # noqa: F401, F403
# 模块3：订单管理
from db.module3_order.orders import *  # noqa: F401, F403
# 模块4：自动化任务
from db.module4_automation.messages import *  # noqa: F401, F403
# 模块5：数据管理
from db.module5_data.history import *  # noqa: F401, F403
from db.module5_data.reports import *  # noqa: F401, F403
from db.module6_credit.credit_history import *  # noqa: F401, F403
from db.module6_credit.customer_credit import *  # noqa: F401, F403
# 模块6：客户信用系统
from db.module6_credit.customer_profiles import (  # noqa: F401, F403
    create_customer_profile, get_customer_by_id, get_customer_by_phone,
    list_customers, set_customer_type, update_customer_profile)
from db.module6_credit.customer_value import *  # noqa: F401, F403
from db.module6_credit.device_profiles import *  # noqa: F401, F403

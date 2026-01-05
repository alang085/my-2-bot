"""模块6信用系统服务 - 统一导出接口"""

from services.module6_credit.credit_service import (get_credit_benefits,
                                                    get_credit_info,
                                                    initialize_credit,
                                                    update_credit_on_breach,
                                                    update_credit_on_payment)
from services.module6_credit.customer_service import (create_customer,
                                                      get_customer)
from services.module6_credit.customer_service import \
    list_customers as list_customers_func
from services.module6_credit.customer_service import (set_customer_type_func,
                                                      update_customer)
from services.module6_credit.value_service import (get_top_customers,
                                                   get_value_info,
                                                   initialize_value,
                                                   update_value_on_order,
                                                   update_value_on_payment)

__all__ = [
    # 客户档案服务
    "create_customer",
    "get_customer",
    "list_customers",
    "update_customer",
    "set_customer_type_func",
    # 信用服务
    "get_credit_info",
    "get_credit_benefits",
    "initialize_credit",
    "update_credit_on_payment",
    "update_credit_on_breach",
    # 价值服务
    "get_value_info",
    "get_top_customers",
    "initialize_value",
    "update_value_on_order",
    "update_value_on_payment",
]

# 导出别名
list_customers = list_customers_func

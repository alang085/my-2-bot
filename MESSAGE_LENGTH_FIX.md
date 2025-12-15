# 报表消息长度问题修复

## 🔍 问题分析

虽然已经有Excel导出功能，但以下地方仍然可能因为消息太长而失败：

1. **订单总表显示**（`show_order_table`）
   - 直接发送 `table_text`，没有检查长度
   - 如果订单很多，会超过Telegram的4096字符限制

2. **报表文本显示**（`generate_report_text`）
   - 虽然统计数据本身不会太长，但理论上也可能超过限制

## 🔧 解决方案

### 方案1：添加消息长度检查和分段发送

在发送消息前检查长度，如果超过限制则：
- 分段发送（每段不超过4000字符）
- 提示用户使用Excel导出功能查看完整数据

### 方案2：当内容太长时，自动建议使用Excel导出

如果检测到内容会超过限制，直接提示用户点击"导出Excel"按钮。

---

## 📝 需要修复的位置

1. `handlers/order_table_handlers.py` - `show_order_table` 函数
2. `handlers/report_handlers.py` - `show_report` 和 `show_my_report` 函数（预防性修复）


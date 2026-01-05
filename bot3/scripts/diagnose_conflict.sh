#!/bin/bash
# 诊断 Conflict 错误的脚本

echo "=== 机器人 Conflict 错误诊断 ==="
echo ""

echo "1. 检查本地进程..."
ps aux | grep "[p]ython.*main.py" && echo "⚠️ 发现本地进程" || echo "✅ 本地无进程"
echo ""

echo "2. 检查网络连接..."
lsof -i -P | grep -i "python\|telegram" | grep -E "149.154|91.108" | head -5 || echo "✅ 无相关网络连接"
echo ""

echo "3. 检查日志中的错误..."
if [ -f "bot_runtime.log" ]; then
    echo "最近的 Conflict 错误:"
    tail -50 bot_runtime.log | grep -i "conflict" | tail -3 || echo "  未发现 Conflict 错误"
else
    echo "  日志文件不存在"
fi
echo ""

echo "=== 建议解决方案 ==="
echo ""
echo "如果 Conflict 错误持续存在，请尝试："
echo ""
echo "1. 检查其他设备/服务器:"
echo "   - 是否在其他电脑或服务器上运行了机器人？"
echo "   - 是否在云平台（如 Zeabur, Heroku）上部署了机器人？"
echo ""
echo "2. 等待更长时间:"
echo "   - Telegram API 可能需要 2-5 分钟才能完全释放连接"
echo "   - 建议等待 3-5 分钟后重试"
echo ""
echo "3. 使用 Webhook 模式（如果适用）:"
echo "   - 如果之前使用过 Webhook，需要先删除 Webhook"
echo "   - 使用命令: curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
echo ""
echo "4. 联系 Telegram 支持:"
echo "   - 如果问题持续，可能需要联系 Telegram 支持重置 Bot Token"


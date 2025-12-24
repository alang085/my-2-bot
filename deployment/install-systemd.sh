#!/bin/bash
# 安装 systemd 服务脚本

set -e

echo "=========================================="
echo "安装 Loan Bot Systemd 服务"
echo "=========================================="

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 root 权限运行此脚本"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 服务文件路径
SERVICE_FILE="/etc/systemd/system/loan-bot.service"

# 复制服务文件
echo "📋 复制服务文件..."
cp "$SCRIPT_DIR/loan-bot.service" "$SERVICE_FILE"

# 更新服务文件中的路径和配置
echo "⚙️  配置服务文件..."
sed -i "s|/app|$PROJECT_ROOT|g" "$SERVICE_FILE"

# 提示用户设置环境变量
echo ""
echo "⚠️  请编辑服务文件以设置环境变量："
echo "   $SERVICE_FILE"
echo ""
echo "需要设置的环境变量："
echo "  - BOT_TOKEN: Telegram Bot Token"
echo "  - ADMIN_USER_IDS: 管理员用户ID列表（逗号分隔）"
echo "  - DATA_DIR: 数据目录路径（可选，默认 /data）"
echo "  - DEBUG: 调试模式（可选，默认 0）"
echo ""
read -p "按 Enter 继续编辑服务文件，或 Ctrl+C 取消..."

# 使用默认编辑器编辑
${EDITOR:-nano} "$SERVICE_FILE"

# 重新加载 systemd
echo "🔄 重新加载 systemd..."
systemctl daemon-reload

# 启用服务
echo "✅ 启用服务..."
systemctl enable loan-bot.service

echo ""
echo "=========================================="
echo "✅ 服务安装完成！"
echo "=========================================="
echo ""
echo "常用命令："
echo "  启动服务:   sudo systemctl start loan-bot"
echo "  停止服务:   sudo systemctl stop loan-bot"
echo "  重启服务:   sudo systemctl restart loan-bot"
echo "  查看状态:   sudo systemctl status loan-bot"
echo "  查看日志:   sudo journalctl -u loan-bot -f"
echo "  查看最近日志: sudo journalctl -u loan-bot -n 100"
echo ""


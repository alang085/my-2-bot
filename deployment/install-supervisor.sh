#!/bin/bash
# 安装 Supervisor 配置脚本

set -e

echo "=========================================="
echo "安装 Loan Bot Supervisor 配置"
echo "=========================================="

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 root 权限运行此脚本"
    exit 1
fi

# 检查 supervisor 是否安装
if ! command -v supervisorctl &> /dev/null; then
    echo "❌ Supervisor 未安装"
    echo "请先安装 Supervisor:"
    echo "  Ubuntu/Debian: sudo apt-get install supervisor"
    echo "  CentOS/RHEL:  sudo yum install supervisor"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 创建日志目录
LOG_DIR="/var/log/loan-bot"
echo "📁 创建日志目录: $LOG_DIR"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# 配置文件路径
CONF_FILE="/etc/supervisor/conf.d/loan-bot.conf"

# 复制配置文件
echo "📋 复制配置文件..."
cp "$SCRIPT_DIR/supervisor.conf" "$CONF_FILE"

# 更新配置文件中的路径
echo "⚙️  配置服务文件..."
sed -i "s|/app|$PROJECT_ROOT|g" "$CONF_FILE"

# 提示用户设置环境变量
echo ""
echo "⚠️  请编辑配置文件以设置环境变量："
echo "   $CONF_FILE"
echo ""
echo "需要设置的环境变量："
echo "  - BOT_TOKEN: Telegram Bot Token"
echo "  - ADMIN_USER_IDS: 管理员用户ID列表（逗号分隔）"
echo "  - DATA_DIR: 数据目录路径（可选，默认 /data）"
echo "  - DEBUG: 调试模式（可选，默认 0）"
echo ""
read -p "按 Enter 继续编辑配置文件，或 Ctrl+C 取消..."

# 使用默认编辑器编辑
${EDITOR:-nano} "$CONF_FILE"

# 重新加载 supervisor
echo "🔄 重新加载 Supervisor..."
supervisorctl reread
supervisorctl update

echo ""
echo "=========================================="
echo "✅ Supervisor 配置完成！"
echo "=========================================="
echo ""
echo "常用命令："
echo "  启动服务:   sudo supervisorctl start loan-bot"
echo "  停止服务:   sudo supervisorctl stop loan-bot"
echo "  重启服务:   sudo supervisorctl restart loan-bot"
echo "  查看状态:   sudo supervisorctl status loan-bot"
echo "  查看日志:   tail -f /var/log/loan-bot/loan-bot.log"
echo "  查看错误日志: tail -f /var/log/loan-bot/loan-bot-error.log"
echo ""


#!/bin/bash
# Linux/Mac 脚本 - 直接修改运行服务上的报表数据

echo "=========================================="
echo "修改报表数据工具"
echo "=========================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 未安装"
    echo "请先安装 Python 3.6+"
    exit 1
fi

# 显示使用说明
if [ $# -eq 0 ]; then
    echo "使用方法:"
    echo "  ./modify_report_data.sh --type financial --field liquid_funds --value 100000 --mode set"
    echo "  ./modify_report_data.sh --type grouped --group_id S01 --field interest --value 5000 --mode add"
    echo "  ./modify_report_data.sh --type daily --date 2025-01-15 --field interest --value 1000 --mode set"
    echo ""
    echo "查看数据:"
    echo "  ./modify_report_data.sh --type financial --show"
    echo "  ./modify_report_data.sh --type grouped --group_id S01 --show"
    echo "  ./modify_report_data.sh --type daily --date 2025-01-15 --show"
    echo ""
    exit 0
fi

# 执行 Python 脚本
python3 scripts/modify_report_data.py "$@"






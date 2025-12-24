#!/bin/bash
# 一次性脚本：将2025-12-22的统计数据（除了延续性数据）全部归零
# 执行方式：bash scripts/reset_daily_data_2025_12_22.sh

echo "========================================"
echo "数据重置脚本"
echo "目标日期: 2025-12-22"
echo "========================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")/.."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "错误: 未找到Python，请先安装Python"
        exit 1
    else
        PYTHON_CMD=python
    fi
else
    PYTHON_CMD=python3
fi

# 执行Python脚本
$PYTHON_CMD scripts/reset_daily_data_2025_12_22.py

if [ $? -ne 0 ]; then
    echo ""
    echo "错误: 脚本执行失败"
    exit 1
else
    echo ""
    echo "脚本执行完成"
fi


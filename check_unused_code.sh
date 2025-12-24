#!/bin/bash
# 检测未使用的代码（死代码检测）

set -e

echo "========================================"
echo "检测未使用的代码"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[1/2] 安装 vulture（如果未安装）...${NC}"
pip install vulture --quiet

echo ""
echo -e "${BLUE}[2/2] 运行死代码检测...${NC}"
echo ""

vulture . --min-confidence 80 --exclude venv,.venv,__pycache__,*.pyc,code-quality-template

echo ""
echo -e "${GREEN}========================================"
echo "检测完成！"
echo "========================================${NC}"
echo ""
echo "说明："
echo "- 高置信度（80%以上）的结果通常是真正的死代码"
echo "- 低置信度可能是误报，需要人工检查"
echo "- 建议先处理高置信度的结果"
echo ""


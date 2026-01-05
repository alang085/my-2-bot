#!/bin/bash
# 生成测试报告脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v pytest &> /dev/null; then
    echo "错误: pytest 未安装"
    exit 1
fi

REPORT_DIR="reports"
mkdir -p "$REPORT_DIR"

pytest tests/ \
    -v \
    --html="$REPORT_DIR/test-report.html" \
    --self-contained-html \
    --cov=. \
    --cov-report=html:"$REPORT_DIR/htmlcov" \
    --cov-report=term-missing \
    --cov-report=json:"$REPORT_DIR/coverage.json" \
    --tb=short

echo -e "${GREEN}报告: ${REPORT_DIR}/test-report.html, ${REPORT_DIR}/htmlcov/index.html${NC}"


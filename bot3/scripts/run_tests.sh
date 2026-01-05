#!/bin/bash
# 测试执行脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v pytest &> /dev/null; then
    echo -e "${RED}错误: pytest 未安装${NC}"
    exit 1
fi

TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    unit) pytest tests/unit/ -v --tb=short ;;
    integration) pytest tests/integration/ -v --tb=short ;;
    functional) pytest tests/functional/ -v --tb=short ;;
    e2e) pytest tests/e2e/ -v --tb=short ;;
    performance) pytest tests/performance/ -v --tb=short ;;
    security) pytest tests/security/ -v --tb=short ;;
    coverage)
        pytest --cov=. --cov-report=html --cov-report=term --cov-report=json
        echo -e "${GREEN}覆盖率报告: htmlcov/index.html${NC}"
        ;;
    report)
        pytest --html=report.html --self-contained-html --cov=. --cov-report=html
        echo -e "${GREEN}报告已生成: report.html, htmlcov/index.html${NC}"
        ;;
    all) pytest tests/ -v --tb=short ;;
    *)
        echo "用法: $0 [unit|integration|functional|e2e|performance|security|coverage|report|all]"
        exit 1
        ;;
esac


#!/bin/bash
# 代码质量工具快速设置脚本 (Linux/Mac)
# 自动检测项目结构并生成配置文件

set -e

echo "========================================"
echo "代码质量工具快速设置"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}[ERROR] 未检测到 Python${NC}"
    echo "请先安装 Python 3.9 或更高版本"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo -e "${GREEN}[OK] Python 已安装${NC}"
$PYTHON_CMD --version
echo ""

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}[WARNING] 未找到 requirements.txt${NC}"
    echo "请确保在项目根目录运行此脚本"
    echo ""
fi

# 复制模板文件
echo -e "${BLUE}[1/4] 复制配置文件模板...${NC}"

if [ ! -f "pyproject.toml" ]; then
    cp "code-quality-template/pyproject.toml.template" "pyproject.toml"
    echo -e "  ${GREEN}[OK] 已创建 pyproject.toml${NC}"
else
    echo -e "  ${YELLOW}[SKIP] pyproject.toml 已存在${NC}"
fi

if [ ! -f "requirements-dev.txt" ]; then
    cp "code-quality-template/requirements-dev.txt.template" "requirements-dev.txt"
    echo -e "  ${GREEN}[OK] 已创建 requirements-dev.txt${NC}"
else
    echo -e "  ${YELLOW}[SKIP] requirements-dev.txt 已存在${NC}"
fi

if [ ! -f "check_code_quality.sh" ]; then
    cp "code-quality-template/check_code_quality.sh.template" "check_code_quality.sh"
    chmod +x check_code_quality.sh
    echo -e "  ${GREEN}[OK] 已创建 check_code_quality.sh${NC}"
else
    echo -e "  ${YELLOW}[SKIP] check_code_quality.sh 已存在${NC}"
fi

echo ""
echo -e "${BLUE}[2/4] 安装开发工具依赖...${NC}"
$PYTHON_CMD -m pip install -r requirements-dev.txt

echo ""
echo -e "${BLUE}[3/4] 检测项目结构...${NC}"
echo "  正在分析项目结构..."

# 检测 Python 模块目录
MODULES=""
if [ -d "src" ]; then
    MODULES="src"
elif [ -d "app" ]; then
    MODULES="app"
else
    # 查找包含 __init__.py 的目录
    for dir in */; do
        if [ -f "${dir}__init__.py" ]; then
            if [ -z "$MODULES" ]; then
                MODULES="${dir%/}"
            else
                MODULES="$MODULES ${dir%/}"
            fi
        fi
    done
fi

if [ -n "$MODULES" ]; then
    echo -e "  ${GREEN}[OK] 检测到模块: $MODULES${NC}"
    echo ""
    echo -e "  ${YELLOW}[提示] 请在 pyproject.toml 中更新 known_first_party 配置${NC}"
    echo "  当前检测到的模块: $MODULES"
else
    echo -e "  ${YELLOW}[INFO] 未检测到标准模块结构，将使用默认配置${NC}"
fi

echo ""
echo -e "${GREEN}[4/4] 完成设置！${NC}"
echo ""
echo "========================================"
echo "下一步操作："
echo "========================================"
echo ""
echo "1. 编辑 pyproject.toml，修改以下配置："
echo "   - known_first_party: 你的项目模块名"
echo "   - mypy.overrides: 你的第三方库"
echo ""
echo "2. 编辑 check_code_quality.sh，修改 pylint 检查路径"
echo ""
echo "3. 运行检查: ./check_code_quality.sh"
echo ""


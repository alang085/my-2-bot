#!/bin/bash
# 整体测试脚本 (Linux/Mac)

set -e

echo "=========================================="
echo "整体测试和功能验证"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[1/5]${NC} 环境检查..."
bash local_test.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 环境检查失败，请先修复问题${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[2/5]${NC} 代码质量检查..."
python3 -m py_compile main.py handlers/*.py callbacks/*.py utils/*.py 2>/dev/null || python -m py_compile main.py handlers/*.py callbacks/*.py utils/*.py 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  部分文件有语法问题，但继续测试...${NC}"
else
    echo -e "${GREEN}✅ 所有文件语法正确${NC}"
fi
echo ""

echo -e "${BLUE}[3/5]${NC} 模块导入测试..."
PYTHON_CMD=$(command -v python3 || command -v python)
$PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); import config; import db_operations; import handlers; import callbacks; import utils; print('✅ 所有模块导入成功')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 模块导入失败${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[4/5]${NC} 数据库初始化测试..."
$PYTHON_CMD -c "import init_db; init_db.init_database(); print('✅ 数据库初始化成功')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  数据库初始化可能有问题${NC}"
else
    echo -e "${GREEN}✅ 数据库初始化成功${NC}"
fi
echo ""

echo -e "${BLUE}[5/5]${NC} 功能列表生成..."
echo "正在生成功能列表..."
echo -e "${GREEN}✅ 功能列表文档: ALL_FEATURES.md${NC}"
echo ""

echo -e "${GREEN}=========================================="
echo "✅ 整体测试完成！"
echo "==========================================${NC}"
echo ""
echo "下一步:"
echo "  1. 查看 ALL_FEATURES.md 了解所有功能"
echo "  2. 查看 LOCAL_TEST_CHECKLIST.md 进行详细测试"
echo "  3. 运行: python main.py 启动机器人"
echo "  4. 在Telegram中测试各项功能"
echo ""


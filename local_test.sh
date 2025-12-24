#!/bin/bash
# 本地测试和细微级别检查脚本 (Linux/Mac)

set -e  # 遇到错误立即退出

echo "=========================================="
echo "本地测试和细微级别检查"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Python版本
echo -e "${BLUE}[1/10]${NC} 检查Python版本..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python未安装${NC}"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# 检查Python版本是否符合要求
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  警告: Python版本可能过低，建议使用3.9+${NC}"
fi
echo ""

# 检查必要文件
echo -e "${BLUE}[2/10]${NC} 检查必要文件..."
required_files=("main.py" "requirements.txt" "init_db.py" "config.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ 所有必要文件存在${NC}"
else
    echo -e "${RED}❌ 缺少必要文件:${NC}"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi
echo ""

# 检查配置文件
echo -e "${BLUE}[3/10]${NC} 检查配置文件..."
if [ -f "user_config.py" ]; then
    echo -e "${GREEN}✅ user_config.py 存在${NC}"
else
    echo -e "${YELLOW}⚠️  user_config.py 不存在，将使用环境变量${NC}"
    if [ -z "$BOT_TOKEN" ]; then
        echo -e "${RED}❌ 环境变量 BOT_TOKEN 未设置${NC}"
        echo "   请创建 user_config.py 或设置环境变量"
        exit 1
    fi
fi
echo ""

# 检查依赖安装
echo -e "${BLUE}[4/10]${NC} 检查Python依赖..."
if ! $PYTHON_CMD -c "import telegram" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  依赖未安装，正在安装...${NC}"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 依赖已安装${NC}"
fi
echo ""

# 检查代码语法
echo -e "${BLUE}[5/10]${NC} 检查代码语法..."
if ! $PYTHON_CMD -m py_compile main.py 2>/dev/null; then
    echo -e "${RED}❌ main.py 语法错误${NC}"
    $PYTHON_CMD -m py_compile main.py
    exit 1
fi
echo -e "${GREEN}✅ main.py 语法正确${NC}"
echo ""

# 检查数据库初始化
echo -e "${BLUE}[6/10]${NC} 检查数据库初始化..."
if ! $PYTHON_CMD -c "import init_db; init_db.init_database()" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  数据库初始化可能有问题，但继续测试...${NC}"
else
    echo -e "${GREEN}✅ 数据库初始化成功${NC}"
fi
echo ""

# 检查导入
echo -e "${BLUE}[7/10]${NC} 检查模块导入..."
if ! $PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); import config; import db_operations; import handlers; import callbacks; import utils" 2>/dev/null; then
    echo -e "${RED}❌ 模块导入失败${NC}"
    $PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); import config; import db_operations; import handlers; import callbacks; import utils"
    exit 1
fi
echo -e "${GREEN}✅ 所有模块导入成功${NC}"
echo ""

# 检查配置加载
echo -e "${BLUE}[8/10]${NC} 检查配置加载..."
if ! $PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); from config import load_config; load_config()" 2>/dev/null; then
    echo -e "${RED}❌ 配置加载失败${NC}"
    echo "   请检查 BOT_TOKEN 和 ADMIN_USER_IDS 是否设置"
    $PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); from config import load_config; load_config()"
    exit 1
fi
echo -e "${GREEN}✅ 配置加载成功${NC}"
echo ""

# 检查数据库连接
echo -e "${BLUE}[9/10]${NC} 检查数据库连接..."
if ! $PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); import db_operations; import asyncio; asyncio.run(db_operations.get_financial_data())" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  数据库连接可能有问题，但继续测试...${NC}"
else
    echo -e "${GREEN}✅ 数据库连接正常${NC}"
fi
echo ""

# 检查代码质量
echo -e "${BLUE}[10/10]${NC} 检查代码质量..."
if command -v flake8 &> /dev/null; then
    echo "运行 flake8 检查..."
    flake8 --max-line-length=100 --ignore=E203,E501,W503 main.py config.py init_db.py 2>/dev/null || true
    echo -e "${GREEN}✅ 代码质量检查完成${NC}"
else
    echo -e "${YELLOW}⚠️  flake8 未安装，跳过代码质量检查${NC}"
    echo "   安装命令: pip install flake8"
fi
echo ""

echo -e "${GREEN}=========================================="
echo "✅ 所有检查完成！"
echo "==========================================${NC}"
echo ""
echo "下一步:"
echo "  1. 确保已设置 BOT_TOKEN 和 ADMIN_USER_IDS"
echo "  2. 运行: python main.py"
echo "  3. 在Telegram中测试机器人功能"
echo ""


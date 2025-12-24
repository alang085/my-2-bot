#!/bin/bash
# Zeabur CLI 快速部署脚本 (Linux/Mac)
# 使用 Zeabur CLI 直接部署，无需 Git 推送

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Zeabur CLI 快速部署"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ 未检测到 Node.js${NC}"
    echo ""
    echo "请先安装 Node.js:"
    echo "  1. 访问 https://nodejs.org/"
    echo "  2. 下载并安装 LTS 版本"
    echo "  3. 或使用包管理器安装:"
    echo "     - Ubuntu/Debian: sudo apt install nodejs npm"
    echo "     - macOS: brew install node"
    echo "     - CentOS/RHEL: sudo yum install nodejs npm"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Node.js 已安装${NC}"
echo "   版本: $(node --version)"
echo ""

# 检查必要文件
echo "检查必要文件..."
required_files=("main.py" "requirements.txt" "Dockerfile" "zeabur.json")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo -e "${RED}❌ 缺少必要文件:${NC}"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo -e "${GREEN}✅ 必要文件检查通过${NC}"
echo ""

# 检查是否已登录
echo "检查 Zeabur 登录状态..."
if ! npx --yes zeabur@latest auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  未登录 Zeabur${NC}"
    echo ""
    echo "正在打开浏览器进行登录..."
    echo "请按照浏览器提示完成登录"
    echo ""
    if ! npx --yes zeabur@latest auth login; then
        echo -e "${RED}❌ 登录失败，请重试${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 登录成功${NC}"
else
    echo -e "${GREEN}✅ 已登录 Zeabur${NC}"
fi
echo ""

# 显示当前配置
echo "当前部署配置:"
echo "  - 启动命令: python main.py"
echo "  - 构建器: DOCKER"
echo "  - 重启策略: ON_FAILURE (最多10次)"
echo ""

# 确认部署
read -p "是否开始部署？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消部署"
    exit 0
fi

echo ""
echo "=========================================="
echo "开始部署..."
echo "=========================================="
echo ""

# 执行部署
if npx --yes zeabur@latest deploy; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 部署成功！"
    echo "==========================================${NC}"
    echo ""
    echo "提示:"
    echo "  - 请在 Zeabur Dashboard 配置环境变量"
    echo "  - 需要设置: BOT_TOKEN, ADMIN_USER_IDS, DATA_DIR"
    echo "  - 需要添加 Volume (挂载路径: /data)"
    echo ""
else
    echo ""
    echo -e "${RED}=========================================="
    echo "❌ 部署失败"
    echo "==========================================${NC}"
    echo ""
    echo "请检查:"
    echo "  1. 网络连接是否正常"
    echo "  2. Zeabur 账户是否有权限"
    echo "  3. 查看上方错误信息"
    echo ""
    exit 1
fi


#!/bin/bash
# Zeabur 部署脚本
# 用于准备和推送代码到 Git 仓库，触发 Zeabur 自动部署

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Zeabur 部署准备脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Git 是否初始化
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git 未初始化，正在初始化...${NC}"
    git init
    echo -e "${GREEN}✅ Git 初始化完成${NC}"
fi

# 检查是否有未提交的更改
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  没有需要提交的更改${NC}"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 显示当前状态
echo ""
echo "当前 Git 状态："
git status --short
echo ""

# 检查敏感文件
echo "检查敏感文件..."
if git ls-files --error-unmatch config.py user_config.py loan_bot.db 2>/dev/null; then
    echo -e "${RED}❌ 发现敏感文件在 Git 跟踪中！${NC}"
    echo "请确保以下文件在 .gitignore 中："
    echo "  - config.py"
    echo "  - user_config.py"
    echo "  - *.db"
    echo "  - temp/"
    exit 1
fi
echo -e "${GREEN}✅ 敏感文件检查通过${NC}"

# 检查必要的文件
echo ""
echo "检查必要文件..."
required_files=("main.py" "init_db.py" "requirements.txt" "Procfile" "Dockerfile")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ 缺少必要文件: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ 必要文件检查通过${NC}"

# 询问提交信息
echo ""
read -p "请输入提交信息 (默认: Update code for Zeabur deployment): " commit_msg
commit_msg=${commit_msg:-"Update code for Zeabur deployment"}

# 添加所有更改
echo ""
echo "添加文件到 Git..."
git add .
echo -e "${GREEN}✅ 文件已添加${NC}"

# 提交更改
echo ""
echo "提交更改..."
git commit -m "$commit_msg"
echo -e "${GREEN}✅ 更改已提交${NC}"

# 检查远程仓库
echo ""
if git remote | grep -q "^origin$"; then
    remote_url=$(git remote get-url origin)
    echo "远程仓库: $remote_url"
    read -p "是否推送到远程仓库？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "推送到远程仓库..."
        branch=$(git branch --show-current)
        git push origin "$branch"
        echo -e "${GREEN}✅ 代码已推送到远程仓库${NC}"
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✅ 部署准备完成！"
        echo "=========================================="
        echo ""
        echo "Zeabur 会自动检测代码更新并重新部署。"
        echo "请在 Zeabur Dashboard 查看部署状态。"
    fi
else
    echo -e "${YELLOW}⚠️  未配置远程仓库${NC}"
    echo ""
    read -p "是否添加远程仓库？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入远程仓库地址: " remote_url
        git remote add origin "$remote_url"
        echo -e "${GREEN}✅ 远程仓库已添加${NC}"
        echo ""
        read -p "是否立即推送？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            branch=$(git branch --show-current)
            git push -u origin "$branch"
            echo -e "${GREEN}✅ 代码已推送到远程仓库${NC}"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "完成！"
echo "=========================================="


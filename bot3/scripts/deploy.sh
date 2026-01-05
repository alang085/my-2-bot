#!/bin/bash
# 部署脚本

set -e  # 遇到错误立即退出

echo "=== bot3 部署脚本 ==="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 检查依赖
echo ""
echo "检查依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 不存在"
    exit 1
fi

# 安装依赖
echo ""
echo "安装依赖..."
pip3 install -r requirements.txt

# 检查环境变量
echo ""
echo "检查环境变量..."
if [ -z "$BOT_TOKEN" ]; then
    echo "⚠️  BOT_TOKEN 未设置"
    if [ -f "user_config.py" ]; then
        echo "✅ 找到 user_config.py，将使用文件中的配置"
    else
        echo "❌ 请设置 BOT_TOKEN 环境变量或创建 user_config.py"
        exit 1
    fi
else
    echo "✅ BOT_TOKEN 已设置"
fi

if [ -z "$ADMIN_USER_IDS" ]; then
    echo "⚠️  ADMIN_USER_IDS 未设置"
    if [ -f "user_config.py" ]; then
        echo "✅ 找到 user_config.py，将使用文件中的配置"
    else
        echo "❌ 请设置 ADMIN_USER_IDS 环境变量或创建 user_config.py"
        exit 1
    fi
else
    echo "✅ ADMIN_USER_IDS 已设置"
fi

# 创建数据目录
echo ""
echo "创建数据目录..."
mkdir -p data
mkdir -p logs

# 运行测试（可选）
if [ "$1" == "--test" ]; then
    echo ""
    echo "运行测试..."
    pytest tests/ -v || echo "⚠️  测试失败，但继续部署"
fi

# 启动机器人
echo ""
echo "=== 部署完成 ==="
echo ""
echo "启动机器人..."
echo "使用以下命令启动:"
echo "  python3 main.py"
echo ""
echo "或使用后台运行:"
echo "  nohup python3 main.py > bot_runtime.log 2>&1 &"
echo ""
echo "查看日志:"
echo "  tail -f bot_runtime.log"


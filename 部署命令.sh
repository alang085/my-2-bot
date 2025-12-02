#!/bin/bash
# 快速部署脚本

echo "=========================================="
echo "开始部署..."
echo "=========================================="

# 进入项目目录
cd /app || {
    echo "❌ 错误: 无法进入 /app 目录"
    exit 1
}

# 拉取最新代码
echo "1️⃣ 拉取最新代码..."
git pull origin main

# 检查是否有更新
if [ $? -eq 0 ]; then
    echo "✅ 代码拉取成功"
else
    echo "❌ 代码拉取失败"
    exit 1
fi

# 显示最新提交
echo ""
echo "最新提交："
git log --oneline -3

echo ""
echo "=========================================="
echo "重启服务..."
echo "=========================================="

# 根据部署方式选择重启命令
# 请根据实际情况取消注释相应的命令

# 方式1: systemd
# sudo systemctl restart loan-bot

# 方式2: Docker
# docker restart <container_name>

# 方式3: PM2
# pm2 restart loan-bot

# 方式4: supervisor
# sudo supervisorctl restart loan-bot

# 方式5: 直接运行
# pkill -f main.py
# nohup python main.py > bot.log 2>&1 &

echo "✅ 部署完成！"
echo ""
echo "请根据你的部署方式手动执行重启命令"


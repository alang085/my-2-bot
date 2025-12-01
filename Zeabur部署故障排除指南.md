# Zeabur 部署故障排除指南

## 🔍 镜像拉取失败 - 完整检查清单

### 步骤 1: 检查本地代码

#### ✅ 确认文件已提交
```bash
# 检查关键文件是否在 Git 中
git ls-files | findstr "Dockerfile zeabur.json requirements.txt runtime.txt Procfile"
```

应该看到：
- ✅ Dockerfile
- ✅ zeabur.json
- ✅ requirements.txt
- ✅ runtime.txt
- ✅ Procfile

#### ✅ 验证 Dockerfile 语法
```bash
# 如果有 Docker，可以测试构建
docker build -t test-bot .
```

### 步骤 2: Zeabur 平台检查

#### 1. 清除构建缓存
1. 进入 Zeabur 项目
2. 找到 **Settings** 或 **设置**
3. 查找 **Clear Build Cache** 或 **清除构建缓存**
4. 点击清除

#### 2. 检查构建器设置
1. 进入项目 **Settings**
2. 查看 **Build Settings** 或 **构建设置**
3. 确认：
   - ✅ Builder: **DOCKER**（不是 NIXPACKS）
   - ✅ Dockerfile Path: `Dockerfile`（或留空，自动检测）
   - ✅ Build Command: 留空（使用 Dockerfile）

#### 3. 检查环境变量
确保已设置：
- ✅ `BOT_TOKEN` - 机器人 Token
- ✅ `ADMIN_USER_IDS` - 管理员用户ID（逗号分隔）
- ✅ `DATA_DIR` - 数据目录（可选，默认 `/data`）

### 步骤 3: 重新部署

1. 点击 **Redeploy** 或 **重新部署**
2. 选择 **Latest Commit** 或 **最新提交**
3. 等待构建完成

### 步骤 4: 查看构建日志

#### 正常构建日志应该包含：

```
Step 1/9 : FROM python:3.11-slim
 ---> [镜像ID]
Step 2/9 : WORKDIR /app
 ---> Running in [容器ID]
Step 3/9 : ENV PYTHONUNBUFFERED=1 ...
 ---> Running in [容器ID]
Step 4/9 : RUN apt-get update ...
 ---> Running in [容器ID]
Step 5/9 : COPY requirements.txt .
 ---> [镜像ID]
Step 6/9 : RUN pip install ...
 ---> Running in [容器ID]
   Collecting python-telegram-bot>=20.0
   Collecting pytz>=2023.3
   Collecting APScheduler>=3.10.0
   Installing collected packages...
Step 7/9 : COPY . .
 ---> [镜像ID]
Step 8/9 : RUN mkdir -p /data
 ---> Running in [容器ID]
Step 9/9 : CMD ["python", "main.py"]
 ---> [镜像ID]
Successfully built [镜像ID]
Successfully tagged [标签]
```

#### 常见错误及解决方案

##### ❌ 错误 1: "failed to pull image"
```
Error: failed to pull image python:3.11-slim
```

**原因**: 网络问题或镜像仓库不可访问

**解决方案**:
1. 检查 Zeabur 平台网络连接
2. 尝试使用其他基础镜像（见下方备选方案）
3. 联系 Zeabur 支持

##### ❌ 错误 2: "Dockerfile not found"
```
Error: Dockerfile not found
```

**原因**: Dockerfile 未提交到 Git 或路径错误

**解决方案**:
```bash
# 确认 Dockerfile 已提交
git add Dockerfile
git commit -m "Add Dockerfile"
git push origin main
```

##### ❌ 错误 3: "pip install failed"
```
Error: pip install failed
```

**原因**: 依赖安装失败

**解决方案**:
1. 检查 `requirements.txt` 格式是否正确
2. 确认所有依赖包名正确
3. 尝试固定版本号（见下方备选方案）

##### ❌ 错误 4: "ModuleNotFoundError"
```
ModuleNotFoundError: No module named 'telegram'
```

**原因**: 依赖未正确安装

**解决方案**:
1. 检查构建日志中是否有 pip install 输出
2. 确认 requirements.txt 已正确复制
3. 尝试在 Dockerfile 中添加调试输出

### 步骤 5: 备选方案

#### 方案 A: 使用 NIXPACKS（如果 Docker 不可用）

如果 Docker 构建器不可用，可以改回 NIXPACKS：

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 方案 B: 使用更稳定的基础镜像

如果 `python:3.11-slim` 拉取失败，可以尝试：

```dockerfile
# 使用官方 Python 镜像（不带 slim）
FROM python:3.11

# 或使用特定版本
FROM python:3.11.0-slim

# 或使用 Alpine（更小，但可能缺少某些库）
FROM python:3.11-alpine
```

#### 方案 C: 固定依赖版本

修改 `requirements.txt`，使用固定版本：

```txt
python-telegram-bot==22.3
pytz==2025.2
APScheduler==3.11.0
```

### 步骤 6: 验证部署

部署成功后，检查：

1. **Runtime Logs** 应该显示：
   ```
   [DEBUG] Project root: /app
   [DEBUG] Current working directory: /app
   机器人启动中...
   管理员数量: X
   检查数据库...
   数据库已就绪
   机器人已启动，等待消息...
   ```

2. **健康检查**:
   - 在 Telegram 中发送 `/start` 给机器人
   - 应该收到回复

### 步骤 7: 如果仍然失败

#### 收集信息
1. **完整的构建日志**（从开始到结束）
2. **Runtime Logs**（如果有）
3. **错误信息**（完整错误堆栈）

#### 联系支持
- Zeabur 支持：在平台内提交工单
- 提供：
  - 项目名称
  - 构建日志
  - 错误信息
  - 已尝试的解决方案

## 📋 快速检查清单

- [ ] Dockerfile 已创建并提交
- [ ] zeabur.json 已更新为 DOCKER 构建器
- [ ] requirements.txt 格式正确
- [ ] 所有文件已推送到 Git
- [ ] Zeabur 环境变量已设置（BOT_TOKEN, ADMIN_USER_IDS）
- [ ] 构建缓存已清除
- [ ] 重新部署已执行
- [ ] 构建日志已检查
- [ ] Runtime Logs 已检查

## 🔧 紧急修复命令

如果需要在本地测试 Docker 构建：

```bash
# 构建镜像
docker build -t loan-bot .

# 运行容器（测试）
docker run --rm -e BOT_TOKEN=test -e ADMIN_USER_IDS=123 loan-bot

# 查看镜像大小
docker images loan-bot
```

## 📝 注意事项

1. **数据持久化**: 确保在 Zeabur 中配置了 Volume，挂载到 `/data`
2. **环境变量**: 不要在代码中硬编码敏感信息
3. **日志**: 定期检查 Runtime Logs，及时发现问题
4. **版本控制**: 保持 Dockerfile 和 requirements.txt 在版本控制中


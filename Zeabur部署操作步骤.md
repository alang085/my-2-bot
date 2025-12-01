# Zeabur 部署操作步骤 - 详细指南

## 📋 操作前检查清单

### ✅ 步骤 0: 本地验证（必须完成）

在开始 Zeabur 操作前，先确认本地代码已准备好：

```bash
# 1. 确认所有关键文件已提交
git status

# 2. 确认关键文件存在
# 应该看到：
# - Dockerfile ✓
# - zeabur.json ✓
# - requirements.txt ✓
# - runtime.txt ✓
# - Procfile ✓
# - main.py ✓
```

---

## 🚀 Zeabur 平台操作步骤

### 步骤 1: 登录并进入项目

1. 打开浏览器，访问 [Zeabur Dashboard](https://dash.zeabur.com)
2. 登录你的账号
3. 找到并点击你的项目（loan005.bot 或类似名称）

---

### 步骤 2: 清除构建缓存

1. 在项目页面，点击左侧菜单的 **"Settings"**（设置）
2. 向下滚动找到 **"Build"** 或 **"构建"** 部分
3. 查找 **"Clear Build Cache"** 或 **"清除构建缓存"** 按钮
4. 点击 **"Clear"** 或 **"清除"** 按钮
5. 等待清除完成（通常几秒钟）

**如果找不到清除缓存选项**：
- 可以直接进行下一步（重新部署会自动清除缓存）

---

### 步骤 3: 检查构建器设置

1. 在 **Settings** 页面，找到 **"Build Settings"** 或 **"构建设置"**
2. 检查以下设置：

   **Builder（构建器）**：
   - ✅ 应该选择 **"DOCKER"** 或 **"Docker"**
   - ❌ 如果是 "NIXPACKS"，需要改为 "DOCKER"

   **Dockerfile Path（Dockerfile 路径）**：
   - ✅ 应该填写 `Dockerfile` 或留空（自动检测）
   - ❌ 不要填写其他路径

   **Build Command（构建命令）**：
   - ✅ 应该留空（使用 Dockerfile 中的默认命令）
   - ❌ 不要填写任何命令

3. 如果设置不正确，修改后点击 **"Save"** 或 **"保存"**

---

### 步骤 4: 检查环境变量

1. 在 **Settings** 页面，找到 **"Environment Variables"** 或 **"环境变量"**
2. 检查以下环境变量是否已设置：

   **必须设置的环境变量**：

   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `BOT_TOKEN` | `你的机器人Token` | 从 @BotFather 获取 |
   | `ADMIN_USER_IDS` | `你的用户ID` | 从 @userinfobot 获取，多个用逗号分隔 |

   **可选环境变量**：

   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `DATA_DIR` | `/data` | 数据目录（用于持久化） |

3. 如果缺少环境变量：
   - 点击 **"Add Variable"** 或 **"添加变量"**
   - 输入变量名和值
   - 点击 **"Save"** 或 **"保存"**

4. 如果环境变量已存在但值不正确：
   - 点击变量右侧的编辑图标
   - 修改值
   - 点击 **"Save"** 或 **"保存"**

---

### 步骤 5: 检查 Volume 配置（数据持久化）

1. 在 **Settings** 页面，找到 **"Volumes"** 或 **"存储卷"**
2. 检查是否有 Volume 配置：

   **如果没有 Volume**：
   - 点击 **"Add Volume"** 或 **"添加存储卷"**
   - Mount Path（挂载路径）：`/data`
   - Size（大小）：`1GB`（可根据需要调整）
   - 点击 **"Create"** 或 **"创建"**

   **如果已有 Volume**：
   - 确认 Mount Path 是 `/data`
   - 如果不是，需要删除后重新创建

---

### 步骤 6: 重新部署

1. 返回项目主页（点击项目名称或左侧菜单的 **"Overview"**）
2. 在页面顶部找到 **"Deployments"** 或 **"部署"** 标签
3. 找到最新的部署记录
4. 点击部署记录右侧的 **"..."** 菜单（三个点）
5. 选择 **"Redeploy"** 或 **"重新部署"**
   
   **或者**：
   
   - 点击页面右上角的 **"Deploy"** 或 **"部署"** 按钮
   - 选择 **"Latest Commit"** 或 **"最新提交"**
   - 点击 **"Deploy"** 或 **"部署"**

6. 等待部署开始（通常几秒钟内会开始）

---

### 步骤 7: 监控构建过程

1. 部署开始后，会自动跳转到构建日志页面
2. 或者点击部署记录查看 **"Build Logs"** 或 **"构建日志"**

3. **观察构建日志**，应该看到：

   ```
   Step 1/9 : FROM python:3.11-slim
   ---> Pulling from library/python
   ---> [镜像ID]
   
   Step 2/9 : WORKDIR /app
   ---> Running in [容器ID]
   ---> [镜像ID]
   
   Step 3/9 : ENV PYTHONUNBUFFERED=1 ...
   ---> Running in [容器ID]
   ---> [镜像ID]
   
   Step 4/9 : RUN apt-get update ...
   ---> Running in [容器ID]
   [输出省略]
   ---> [镜像ID]
   
   Step 5/9 : COPY requirements.txt .
   ---> [镜像ID]
   
   Step 6/9 : RUN pip install ...
   ---> Running in [容器ID]
   Collecting python-telegram-bot>=20.0
   Collecting pytz>=2023.3
   Collecting APScheduler>=3.10.0
   Installing collected packages...
   [输出省略]
   ---> [镜像ID]
   
   Step 7/9 : COPY . .
   ---> [镜像ID]
   
   Step 8/9 : RUN mkdir -p /data
   ---> Running in [容器ID]
   ---> [镜像ID]
   
   Step 9/9 : CMD ["python", "main.py"]
   ---> [镜像ID]
   
   Successfully built [镜像ID]
   Successfully tagged [标签]
   ```

4. **如果看到错误**：
   - 记录完整的错误信息
   - 参考下方的"常见错误处理"

---

### 步骤 8: 检查运行时日志

1. 构建成功后，查看 **"Runtime Logs"** 或 **"运行时日志"**
2. 应该看到：

   ```
   [DEBUG] Project root: /app
   [DEBUG] Current working directory: /app
   [DEBUG] Python path includes project root: True
   [DEBUG] Handlers directory exists: True
   机器人启动中...
   管理员数量: X
   检查数据库...
   数据库已就绪
   机器人已启动，等待消息...
   ```

3. **如果看到错误**：
   - 记录完整的错误信息
   - 参考下方的"常见错误处理"

---

### 步骤 9: 验证部署成功

1. 打开 Telegram
2. 找到你的机器人（通过 @BotFather 创建的机器人）
3. 发送命令：`/start`
4. **应该收到回复**（说明机器人正常运行）

5. **如果收到回复**：
   - ✅ 部署成功！
   - 可以开始使用机器人

6. **如果没有收到回复**：
   - 检查 Runtime Logs 中的错误信息
   - 检查环境变量是否正确设置
   - 参考下方的"常见错误处理"

---

## ❌ 常见错误处理

### 错误 1: "failed to pull image python:3.11-slim"

**症状**：
```
Error: failed to pull image python:3.11-slim
```

**解决方案**：
1. 修改 Dockerfile，将第一行改为：
   ```dockerfile
   FROM python:3.11
   ```
2. 提交更改：
   ```bash
   git add Dockerfile
   git commit -m "Fix: use python:3.11 instead of python:3.11-slim"
   git push origin main
   ```
3. 在 Zeabur 重新部署

---

### 错误 2: "Dockerfile not found"

**症状**：
```
Error: Dockerfile not found
```

**解决方案**：
1. 确认 Dockerfile 已提交到 Git：
   ```bash
   git ls-files Dockerfile
   ```
   应该显示 `Dockerfile`

2. 如果没有，添加并提交：
   ```bash
   git add Dockerfile
   git commit -m "Add Dockerfile"
   git push origin main
   ```

3. 在 Zeabur 重新部署

---

### 错误 3: "ModuleNotFoundError: No module named 'telegram'"

**症状**：
```
ModuleNotFoundError: No module named 'telegram'
```

**解决方案**：
1. 检查构建日志中是否有 pip install 的输出
2. 如果没有，说明依赖安装失败
3. 检查 requirements.txt 格式是否正确
4. 确认 requirements.txt 已提交到 Git

---

### 错误 4: "BOT_TOKEN 未设置"

**症状**：
```
❌ 错误: BOT_TOKEN 未设置
```

**解决方案**：
1. 在 Zeabur Settings → Environment Variables
2. 添加环境变量：
   - 变量名：`BOT_TOKEN`
   - 变量值：你的机器人 Token（从 @BotFather 获取）
3. 保存后重新部署

---

### 错误 5: "ADMIN_USER_IDS 未设置"

**症状**：
```
❌ 错误: ADMIN_USER_IDS 未设置
```

**解决方案**：
1. 在 Zeabur Settings → Environment Variables
2. 添加环境变量：
   - 变量名：`ADMIN_USER_IDS`
   - 变量值：你的用户ID（从 @userinfobot 获取，多个用逗号分隔）
3. 保存后重新部署

---

## 📞 需要帮助？

如果按照以上步骤操作后仍然失败：

1. **收集信息**：
   - 完整的构建日志（Build Logs）
   - 完整的运行时日志（Runtime Logs）
   - 错误信息截图

2. **检查清单**：
   - [ ] Dockerfile 已提交到 Git
   - [ ] zeabur.json 已提交到 Git
   - [ ] requirements.txt 已提交到 Git
   - [ ] 环境变量已正确设置
   - [ ] 构建器设置为 DOCKER
   - [ ] 已清除构建缓存
   - [ ] 已重新部署

3. **联系支持**：
   - 在 Zeabur 平台提交工单
   - 或在项目 Issues 中报告问题

---

## ✅ 成功标志

部署成功的标志：

- ✅ 构建日志显示 "Successfully built"
- ✅ 运行时日志显示 "机器人已启动，等待消息..."
- ✅ 在 Telegram 中发送 `/start` 收到回复
- ✅ 没有错误信息

---

## 📝 操作记录

记录你的操作过程：

- [ ] 步骤 1: 已登录并进入项目
- [ ] 步骤 2: 已清除构建缓存
- [ ] 步骤 3: 已检查构建器设置（DOCKER）
- [ ] 步骤 4: 已检查环境变量（BOT_TOKEN, ADMIN_USER_IDS）
- [ ] 步骤 5: 已检查 Volume 配置
- [ ] 步骤 6: 已重新部署
- [ ] 步骤 7: 已监控构建过程
- [ ] 步骤 8: 已检查运行时日志
- [ ] 步骤 9: 已验证部署成功（Telegram 测试通过）

---

**最后更新**: 2025-01-XX
**版本**: 1.0


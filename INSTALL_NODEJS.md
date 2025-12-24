# Node.js 安装指南（用于 Zeabur CLI 部署）

## 📥 安装步骤

### 1. 下载 Node.js

**推荐方式**：
- 访问官网：https://nodejs.org/
- 下载 **LTS 版本**（长期支持版本，更稳定）
- 当前推荐版本：v20.x.x 或 v18.x.x

**直接下载链接**：
- Windows 64-bit: https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi
- 或访问官网获取最新 LTS 版本

### 2. 安装 Node.js

1. **运行安装程序**
   - 双击下载的 `.msi` 文件
   - 按照安装向导操作

2. **安装选项**（推荐）
   - ✅ 勾选 "Automatically install the necessary tools"
   - ✅ 勾选 "Add to PATH"（重要！）
   - 其他选项保持默认即可

3. **完成安装**
   - 点击 "Finish" 完成安装
   - **重要**：关闭并重新打开终端/PowerShell

### 3. 验证安装

打开新的终端/PowerShell，运行：

```bash
# 检查 Node.js 版本
node --version

# 检查 npm 版本（Node.js 自带）
npm --version
```

**预期输出**：
```
v20.11.0
10.2.4
```

### 4. 如果验证失败

**问题**：`node` 命令无法识别

**解决方案**：
1. 检查环境变量 PATH
   - 打开 "系统属性" → "环境变量"
   - 确认 PATH 中包含 Node.js 安装路径（通常是 `C:\Program Files\nodejs\`）

2. 重启终端
   - 完全关闭 PowerShell/CMD
   - 重新打开

3. 手动添加 PATH（如果自动添加失败）
   - 将 Node.js 安装路径添加到系统 PATH

## 🚀 安装完成后部署

### 1. 验证 Node.js 已安装

```bash
node --version
```

### 2. 运行部署脚本

```bash
deploy_zeabur_cli.bat
```

### 3. 脚本会自动：

- ✅ 检查 Node.js 是否安装
- ✅ 检查必要文件是否存在
- ✅ 检查 Zeabur 登录状态（未登录会自动打开浏览器登录）
- ✅ 执行部署命令

### 4. 首次使用需要登录

脚本会自动打开浏览器，按照提示完成 Zeabur 账户登录。

## ⚠️ 常见问题

### Q: 安装后仍然提示 "未检测到 Node.js"

**A**: 
1. 确认已重启终端
2. 运行 `where node` 检查是否在 PATH 中
3. 手动添加 Node.js 路径到系统 PATH

### Q: npm 命令无法使用

**A**: Node.js 安装包自带 npm，如果无法使用，尝试重新安装 Node.js

### Q: 安装速度慢

**A**: 
- 使用国内镜像（可选）：
  ```bash
  npm config set registry https://registry.npmmirror.com
  ```

## 📝 下一步

安装完成后，运行：

```bash
deploy_zeabur_cli.bat
```

脚本会自动完成所有检查和部署步骤！


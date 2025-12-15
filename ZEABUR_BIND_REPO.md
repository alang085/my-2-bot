# Zeabur 绑定 GitHub 仓库步骤

## 📋 前置准备

- ✅ GitHub 仓库已准备好（你的仓库：`alang095-hub/my-telegram-bot111`）
- ✅ 代码已推送到 GitHub
- ✅ 有 Zeabur 账户（如果没有，先注册：https://dash.zeabur.com）

---

## 🚀 详细步骤

### 步骤1：登录 Zeabur

1. 访问 [Zeabur Dashboard](https://dash.zeabur.com)
2. 使用 GitHub 账户登录（推荐，方便授权）
   - 或者使用邮箱注册/登录

### 步骤2：创建新项目

1. 在 Zeabur Dashboard 首页，点击 **"New Project"**（新建项目）按钮
2. 或者点击左侧菜单的 **"Projects"** → **"New Project"**

### 步骤3：连接 Git 仓库

1. 选择 **"Import from Git"**（从 Git 导入）
2. 选择 Git 提供商：
   - 如果使用 GitHub 登录，直接选择 **GitHub**
   - 如果没有授权，点击 **"Connect GitHub"** 进行授权
   
3. **授权 GitHub 访问**（如果首次使用）：
   - 点击后会跳转到 GitHub 授权页面
   - 点击 **"Authorize zeabur"** 授权
   - 可以选择授权所有仓库，或只授权特定仓库

### 步骤4：选择仓库和分支

1. **选择仓库**：
   - 在仓库列表中找到：`alang095-hub/my-telegram-bot111`
   - 或者直接搜索：`my-telegram-bot111`
   - 点击选择该仓库

2. **选择分支**：
   - 默认选择 `main` 分支（通常已自动选择）
   - 确认分支名称正确

3. **选择根目录**：
   - 通常默认为 `/`（根目录）
   - 如果你的代码不在仓库根目录，可以选择子目录
   - 对于你的项目，选择 `/` 即可

### 步骤5：配置项目（可选，稍后也可配置）

1. **项目名称**：
   - 可以保持默认名称
   - 或改为：`loan-bot`、`telegram-order-bot` 等

2. **点击 "Deploy" 或 "Create Project"**：
   - 会开始构建项目
   - 第一次构建可能需要几分钟

---

## 🔧 如果看不到仓库？

### 问题1：GitHub 未授权

**解决**：
1. 在 Zeabur Dashboard 中，点击右上角头像
2. 选择 **Settings** 或 **Account Settings**
3. 找到 **Git Providers** 或 **Connections**
4. 点击 **Connect GitHub** 重新授权
5. 确保授权了仓库访问权限

### 问题2：仓库是私有的

**解决**：
1. 确保 GitHub 授权时选择了该私有仓库
2. 或者将仓库设为 Public（临时），部署后再改回 Private

### 问题3：找不到仓库

**解决**：
1. 确认仓库名称：`my-telegram-bot111`
2. 确认仓库所有者：`alang095-hub`
3. 尝试刷新仓库列表
4. 检查 GitHub 账户是否正确授权

---

## 📸 步骤示意图（文字描述）

```
Zeabur Dashboard
  └─> New Project
      └─> Import from Git
          └─> Connect GitHub (如果未授权)
              └─> Authorize zeabur (在GitHub)
                  └─> 选择仓库: my-telegram-bot111
                      └─> 选择分支: main
                          └─> 根目录: /
                              └─> Deploy
```

---

## ✅ 绑定成功后的操作

绑定成功后，接下来需要：

1. **配置 Volume**（持久化存储）
   - 在项目设置中找到 "Storage" 或 "Volumes"
   - 添加 Volume，Mount Path: `/data`

2. **配置环境变量**
   ```
   BOT_TOKEN=你的机器人Token
   ADMIN_USER_IDS=你的用户ID
   DATA_DIR=/data
   ```

3. **上传数据库文件**（如果需要迁移数据）

详细步骤请参考：`DEPLOYMENT_PLAN.md`

---

## 🆘 需要帮助？

如果遇到问题：
- 查看 Zeabur 文档：https://zeabur.com/docs
- 检查 GitHub 授权状态
- 确认仓库权限
- 查看 Zeabur 构建日志中的错误信息


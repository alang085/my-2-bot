# GitLab 设置和推送指南

## 📋 步骤概览

1. 在 GitLab 创建仓库
2. 推送代码到 GitLab
3. 在 Zeabur 连接 GitLab

---

## 🚀 详细步骤

### 步骤1：在 GitLab 创建仓库

1. **访问 GitLab**：
   - 打开：https://gitlab.com
   - 如果没有账户，点击 "Register" 注册
   - 如果有账户，直接登录

2. **创建新项目**：
   - 点击右上角 "+" 按钮
   - 选择 **"New project"** 或 **"Create blank project"**

3. **填写项目信息**：
   - **Project name**: `loan-bot`（或你喜欢的名字）
   - **Project slug**: 会自动生成（通常和项目名相同）
   - **Visibility Level**:
     - ✅ **Private**（推荐）- 只有你能看到
     - 或 **Public** - 所有人可见
   - ⚠️ **不要勾选** "Initialize repository with a README"
   - ⚠️ **不要选择** "Add .gitignore" 或 "Choose a license"

4. **点击 "Create project"**

5. **复制仓库地址**：
   - 创建后会显示仓库地址
   - 格式：`https://gitlab.com/<你的用户名>/<仓库名>.git`
   - 例如：`https://gitlab.com/username/loan-bot.git`
   - **请复制这个地址，稍后需要用到**

---

### 步骤2：推送代码到 GitLab

创建好仓库后，告诉我你的 GitLab 仓库地址，我会帮你配置并推送。

或者你可以自己运行：

```bash
# 添加 GitLab 作为新的远程仓库（保留GitHub作为备份）
git remote add gitlab https://gitlab.com/<你的用户名>/<仓库名>.git

# 推送代码到 GitLab
git push -u gitlab main --force

# 或者替换现有的 origin（如果确定只用GitLab）
# git remote set-url origin https://gitlab.com/<你的用户名>/<仓库名>.git
# git push -u origin main --force
```

---

### 步骤3：在 Zeabur 连接 GitLab

1. **在 Zeabur Dashboard**：
   - 点击 "New Project"
   - 选择 "Import from Git"

2. **选择 GitLab**：
   - 选择 **GitLab**（不是 GitHub）
   - 如果首次使用，点击 "Connect GitLab" 授权

3. **授权 GitLab**：
   - 会跳转到 GitLab 授权页面
   - 点击 "Authorize zeabur"
   - 可以选择授权所有项目，或只授权特定项目

4. **选择仓库**：
   - 在仓库列表中找到你刚创建的仓库
   - 选择分支：`main`
   - 根目录：`/`

5. **开始部署**：
   - 点击 "Deploy"

---

## 🔐 GitLab 认证

推送代码时，GitLab 可能需要认证：

### 方法1：使用 Personal Access Token（推荐）

1. **创建 Token**：
   - 访问：https://gitlab.com/-/user_settings/personal_access_tokens
   - 或：GitLab → 右上角头像 → Preferences → Access Tokens
   - Token name: `zeabur-deployment`
   - Scopes: 勾选 **`write_repository`** 和 **`read_repository`**
   - 点击 "Create personal access token"
   - **复制 Token**（只显示一次）

2. **使用 Token 推送**：
   ```bash
   git remote set-url origin https://oauth2:<TOKEN>@gitlab.com/<用户名>/<仓库名>.git
   git push -u origin main --force
   ```

### 方法2：使用用户名和密码

GitLab 现在通常需要 Personal Access Token，不再支持密码。

---

## ✅ 优势

使用 GitLab 的优势：
- ✅ 更稳定，不容易被暂停
- ✅ 免费私有仓库
- ✅ 功能与 GitHub 类似
- ✅ Zeabur 完全支持
- ✅ 通常授权流程更顺畅

---

## 📝 下一步

1. 在 GitLab 创建仓库
2. 告诉我仓库地址，我帮你推送代码
3. 在 Zeabur 连接 GitLab 并部署

准备好了告诉我！


# GitLab 快速开始

## 🌐 GitLab 链接

### 主站
- **GitLab.com**: https://gitlab.com

### 直接链接
- **注册**: https://gitlab.com/users/sign_up
- **登录**: https://gitlab.com/users/sign_in
- **创建项目**: https://gitlab.com/projects/new

---

## 📝 创建仓库步骤

### 1. 注册/登录
- 访问：https://gitlab.com
- 如果没有账户，点击 "Register" 注册
- 如果有账户，点击 "Sign in" 登录

### 2. 创建新项目

**方法A：通过顶部导航**
1. 登录后，点击右上角 **"+"** 按钮
2. 选择 **"New project/repository"**
3. 选择 **"Create blank project"**

**方法B：直接链接**
- 访问：https://gitlab.com/projects/new
- 选择 **"Create blank project"**

### 3. 填写项目信息

**必填项**：
- **Project name**: `loan-bot`（或你喜欢的名字）
- **Project slug**: 会自动生成（通常和项目名相同）

**选项**：
- **Visibility Level**:
  - ✅ **Private**（推荐，只有你能看到）
  - 或 **Internal**（组织内可见）
  - 或 **Public**（所有人可见）

**重要：不要勾选以下选项**：
- ❌ 不要勾选 "Initialize repository with a README"
- ❌ 不要选择 "Add .gitignore"
- ❌ 不要选择 "Choose a license"

因为这些会在推送时产生冲突。

### 4. 创建项目

点击 **"Create project"** 按钮

### 5. 复制仓库地址

创建成功后，会显示仓库信息，复制仓库地址：

**格式**：`https://gitlab.com/<你的用户名>/<仓库名>.git`

例如：`https://gitlab.com/john/loan-bot.git`

---

## 📋 下一步

创建好仓库后：

1. **复制仓库地址**（完整URL）
2. **告诉我仓库地址**
3. 我会帮你配置并推送代码

或者你也可以参考 `GITLAB_SETUP.md` 文档自己操作。

---

## 🔗 有用的 GitLab 链接

- **我的项目**: https://gitlab.com/dashboard/projects
- **用户设置**: https://gitlab.com/-/user_settings/profile
- **Access Tokens**: https://gitlab.com/-/user_settings/personal_access_tokens
- **SSH Keys**: https://gitlab.com/-/user_settings/ssh_keys


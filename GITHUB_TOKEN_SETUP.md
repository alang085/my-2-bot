# GitHub Personal Access Token 设置指南

## 步骤1：在 GitHub 创建 Personal Access Token

### 1.1 访问 Token 设置页面

1. 登录 GitHub
2. 点击右上角头像
3. 选择 **Settings**（设置）
4. 在左侧菜单找到 **Developer settings**（开发者设置）
5. 点击 **Personal access tokens** → **Tokens (classic)**
6. 或者直接访问：https://github.com/settings/tokens

### 1.2 创建新 Token

1. 点击 **Generate new token** → **Generate new token (classic)**
2. 填写信息：
   - **Note**（备注）：`loan-bot-deployment` 或任意描述
   - **Expiration**（过期时间）：选择合适的时间（建议90天或更长）
   - **Select scopes**（选择权限）：
     - ✅ **repo**（完整仓库访问权限）
       - ✅ repo:status
       - ✅ repo_deployment
       - ✅ public_repo
       - ✅ repo:invite
       - ✅ security_events
     - ✅ **workflow**（如果使用 GitHub Actions）

3. 滚动到底部，点击 **Generate token**

### 1.3 复制 Token

⚠️ **重要**：Token 只会显示一次，请立即复制并保存！

- Token 格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- 请保存在安全的地方

## 步骤2：使用 Token 推送代码

### 方法1：在 URL 中包含 Token（临时使用）

```bash
git remote set-url origin https://<你的用户名>:<token>@github.com/alang095-hub/my-telegram-bot111.git
git push -u origin main
```

### 方法2：使用 Git Credential Manager（推荐）

Windows 通常会自动保存凭证。

## 注意事项

- Token 相当于密码，请保密
- 不要在代码中提交 Token
- Token 过期后需要重新创建
- 如果账户被暂停，Token 也可能无法使用


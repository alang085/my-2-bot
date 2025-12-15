# Zeabur GitHub 授权问题排查

## 🔍 问题：授权后无法继续

在GitHub授权页面点击"允许所有仓库"后，到了仓库页面无法继续。

---

## 🛠️ 解决方案

### 方案1：刷新页面（最简单）

1. **在Zeabur仓库选择页面，按 `F5` 或点击刷新按钮**
2. 仓库列表应该会重新加载
3. 尝试再次选择仓库

### 方案2：重新授权流程

1. **关闭当前页面**（如果卡住了）

2. **重新开始**：
   - 在Zeabur Dashboard，点击 "New Project"
   - 选择 "Import from Git"
   - 再次选择 GitHub

3. **检查授权状态**：
   - 在Zeabur设置中检查GitHub连接状态
   - 如果显示已连接，尝试断开后重新连接

### 方案3：手动检查授权

1. **在GitHub检查授权**：
   - 访问：https://github.com/settings/applications
   - 查看 "Authorized OAuth Apps" 或 "Authorized GitHub Apps"
   - 找到 "Zeabur" 应用
   - 确认授权状态是 "Active"

2. **如果授权不存在或过期**：
   - 在Zeabur中重新授权
   - 确保完成整个授权流程

### 方案4：清除浏览器缓存

1. **清除缓存和Cookie**：
   - 按 `Ctrl + Shift + Delete`
   - 清除最近1小时的缓存和Cookie
   - 重新登录Zeabur和GitHub

2. **使用隐私/无痕模式**：
   - 打开浏览器隐私模式
   - 重新尝试授权流程

### 方案5：使用不同的浏览器

1. **尝试其他浏览器**：
   - Chrome、Firefox、Edge等
   - 有时浏览器扩展会影响授权流程

---

## 🔄 完整重新授权流程

如果以上方法都不行，尝试完全重新授权：

### 步骤1：在GitHub撤销授权

1. 访问：https://github.com/settings/applications
2. 找到 "Zeabur" 应用
3. 点击 "Revoke"（撤销）或删除授权

### 步骤2：在Zeabur断开连接

1. 在Zeabur Dashboard，点击右上角头像
2. 选择 **Settings** 或 **Account Settings**
3. 找到 **Git Providers** 或 **Connections**
4. 找到GitHub连接，点击 **Disconnect** 或 **Remove**

### 步骤3：重新连接

1. 回到 "New Project" → "Import from Git"
2. 选择 GitHub
3. 点击 "Connect GitHub"
4. 完成授权流程

---

## ⚠️ 常见问题

### 问题1：授权后页面空白

**解决**：
- 等待几秒钟，有时需要加载时间
- 检查浏览器控制台是否有错误（F12）
- 尝试刷新页面

### 问题2：仓库列表为空

**可能原因**：
- 授权时没有选择正确的权限
- 账户下没有仓库
- 授权未完成

**解决**：
- 重新授权，确保选择"允许所有仓库"
- 检查GitHub账户下是否有仓库

### 问题3：点击仓库无反应

**解决**：
- 检查是否选择了正确的仓库
- 尝试点击仓库名称而非图标
- 检查是否有JavaScript错误

### 问题4：一直跳转到授权页面

**解决**：
- 清除浏览器缓存
- 使用隐私模式
- 检查是否被广告拦截器阻止

---

## 🎯 推荐操作顺序

1. ✅ **首先尝试**：刷新页面（F5）
2. ✅ **如果不行**：重新开始授权流程
3. ✅ **还不行**：检查GitHub授权状态
4. ✅ **最后**：完全重新授权

---

## 📞 如果还是不行

1. **检查Zeabur状态**：
   - 访问：https://status.zeabur.com
   - 确认服务是否正常

2. **联系支持**：
   - Zeabur支持：https://zeabur.com/docs
   - 或通过Discord社区获取帮助

3. **临时方案**：
   - 可以考虑使用GitLab或其他Git提供商
   - Zeabur也支持GitLab

---

## 💡 小技巧

- 使用Chrome或Edge浏览器通常更稳定
- 确保浏览器已更新到最新版本
- 禁用可能干扰的浏览器扩展
- 确保网络连接稳定


# CI/CD 验证指南

**版本**: 1.0  
**创建日期**: 2025-01-28  
**最后更新**: 2025-01-28

---

## 📋 概述

本文档说明如何在GitHub上设置和验证CI/CD工作流。

---

## 🚀 GitHub Actions工作流配置

### 配置文件位置

`.github/workflows/test.yml`

### 工作流包含的任务

1. **测试任务** (`test`)
   - 支持Python 3.9, 3.10, 3.11
   - 运行单元测试、集成测试、功能测试
   - 生成测试报告和覆盖率报告
   - 上传覆盖率到Codecov
   - 上传测试报告作为Artifact

2. **代码风格检查任务** (`lint`)
   - Black代码格式化检查
   - isort导入排序检查
   - pylint代码质量检查
   - flake8代码风格检查

3. **安全扫描任务** (`security`)
   - Bandit安全扫描
   - 上传安全报告

---

## ✅ 在GitHub上验证CI/CD

### 步骤1：推送代码到GitHub

```bash
# 添加所有文件
git add .

# 提交更改
git commit -m "添加测试代码和CI/CD配置"

# 推送到GitHub（确保有远程仓库）
git push origin main
```

### 步骤2：在GitHub上查看Actions

1. 打开GitHub仓库页面
2. 点击 "Actions" 标签
3. 查看工作流运行状态

### 步骤3：查看测试结果

1. 点击运行中的工作流
2. 查看每个任务的输出
3. 检查测试通过/失败情况

### 步骤4：下载Artifacts

1. 在工作流运行页面底部找到 "Artifacts"
2. 下载测试报告和覆盖率报告
3. 查看HTML报告

---

## 🔧 本地验证CI/CD配置

### 方法1：使用act工具（推荐）

`act` 是一个可以在本地运行GitHub Actions的工具。

#### 安装act

**macOS**:
```bash
brew install act
```

**Linux**:
```bash
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Windows**:
```bash
choco install act-cli
```

#### 运行工作流

```bash
cd bot3

# 列出可用的工作流
act -l

# 运行测试工作流
act push

# 运行特定任务
act -j test
act -j lint
act -j security
```

**注意**：act需要在Docker环境中运行，确保Docker已安装并运行。

### 方法2：手动运行测试脚本

由于GitHub Actions工作流主要是调用pytest，可以在本地运行相同的命令：

```bash
cd bot3

# 运行测试（模拟CI环境）
pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing

# 运行代码风格检查
black --check .
isort --check .
pylint bot3/ --disable=C,R,W || true
flake8 bot3/ --max-line-length=100 --ignore=E501,W503 || true

# 运行安全扫描
bandit -r bot3/ -f json -o bandit-report.json || true
```

---

## 📊 查看测试报告

### 本地生成报告

```bash
cd bot3

# 使用提供的脚本
./scripts/generate_test_report.sh

# 或手动运行
pytest tests/ \
    -v \
    --html=test-report.html \
    --self-contained-html \
    --cov=. \
    --cov-report=html:htmlcov \
    --cov-report=term-missing

# 打开报告
open test-report.html
open htmlcov/index.html
```

### GitHub Artifacts

1. 在工作流运行页面下载Artifacts
2. 解压下载的文件
3. 打开HTML报告查看结果

---

## 🔍 常见问题

### 问题1：工作流未触发

**原因**：
- 工作流文件路径不正确
- 触发条件不匹配
- 工作流文件语法错误

**解决方案**：
1. 检查文件路径：`.github/workflows/test.yml`
2. 检查触发条件（push到main/develop分支）
3. 使用GitHub Actions语法检查器验证YAML文件

### 问题2：测试失败

**原因**：
- 代码有错误
- 测试环境配置问题
- 依赖未安装

**解决方案**：
1. 查看测试输出日志
2. 在本地运行相同的测试命令
3. 检查依赖是否正确安装

### 问题3：覆盖率报告未生成

**原因**：
- pytest-cov未安装
- 覆盖率配置错误

**解决方案**：
1. 确保安装了pytest-cov：`pip install pytest-cov`
2. 检查pytest.ini配置
3. 查看工作流日志中的错误信息

### 问题4：代码风格检查失败

**原因**：
- 代码格式不符合Black/isort规范
- 代码质量问题

**解决方案**：
1. 运行格式化工具：`black . && isort .`
2. 修复pylint/flake8报告的问题
3. 提交格式化后的代码

---

## 📈 持续集成最佳实践

### 1. 保持测试快速

- 单元测试应该快速执行（< 1秒每个测试）
- 集成测试可以稍慢，但应控制在合理范围内
- 使用并行执行：`pytest -n auto`

### 2. 测试隔离

- 每个测试应该独立运行
- 使用fixtures确保测试数据隔离
- 避免测试之间的依赖

### 3. 失败时快速反馈

- 配置通知（邮件、Slack等）
- 使用GitHub Status Checks
- 及时修复失败的测试

### 4. 覆盖率目标

- 设置合理的覆盖率目标（建议80%+）
- 关注关键业务逻辑的覆盖率
- 使用覆盖率报告识别未测试的代码

### 5. 定期审查

- 定期审查CI/CD配置
- 更新依赖版本
- 优化测试执行时间

---

## 🔐 安全考虑

### 敏感信息

- **永远不要**在代码中硬编码敏感信息（API密钥、密码等）
- 使用GitHub Secrets存储敏感信息
- 在`.gitignore`中排除配置文件

### 示例：使用Secrets

```yaml
# .github/workflows/test.yml
env:
  BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
  ADMIN_USER_IDS: ${{ secrets.ADMIN_USER_IDS }}
```

### 设置Secrets

1. 打开GitHub仓库设置
2. 进入 "Secrets and variables" > "Actions"
3. 点击 "New repository secret"
4. 添加敏感信息

---

## 📚 相关文档

- [GitHub Actions文档](https://docs.github.com/en/actions)
- [pytest文档](https://docs.pytest.org/)
- [测试计划](./TEST_PLAN.md)
- [测试实施说明](./TEST_IMPLEMENTATION.md)

---

## 🎯 下一步

1. ✅ 推送代码到GitHub
2. ✅ 验证工作流运行
3. ✅ 查看测试报告
4. ✅ 修复任何失败
5. ✅ 设置代码覆盖率要求
6. ✅ 配置通知（可选）

---

**维护者**: 开发团队  
**最后更新**: 2025-01-28


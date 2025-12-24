# 代码质量检查工具模板

这是一个通用的 Python 项目代码质量检查工具模板，可以快速应用到任何 Python 项目中。

## 📋 包含的工具

1. **Black** - 代码格式化
2. **isort** - 导入排序
3. **flake8** - 代码风格检查
4. **pylint** - 代码质量检查
5. **mypy** - 类型检查
6. **bandit** - 安全检查
7. **radon** - 复杂度检查

## 🚀 快速开始

### 方法一：使用自动设置脚本（推荐）

**Windows:**
```bash
# 1. 复制模板目录到你的项目
xcopy /E /I code-quality-template your-project-path\code-quality-template

# 2. 进入项目目录
cd your-project-path

# 3. 运行设置脚本
code-quality-template\setup_code_quality.bat
```

**Linux/Mac:**
```bash
# 1. 复制模板目录到你的项目
cp -r code-quality-template /path/to/your-project/

# 2. 进入项目目录
cd /path/to/your-project

# 3. 运行设置脚本
chmod +x code-quality-template/setup_code_quality.sh
./code-quality-template/setup_code_quality.sh
```

### 方法二：手动设置

1. **复制模板文件到项目根目录**
   ```bash
   # 复制配置文件
   cp code-quality-template/pyproject.toml.template pyproject.toml
   cp code-quality-template/requirements-dev.txt.template requirements-dev.txt
   cp code-quality-template/check_code_quality.bat.template check_code_quality.bat
   cp code-quality-template/check_code_quality.sh.template check_code_quality.sh
   chmod +x check_code_quality.sh  # Linux/Mac
   ```

2. **安装开发工具**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **修改配置文件**
   - 编辑 `pyproject.toml`，修改 `known_first_party` 为你的项目模块名
   - 编辑 `check_code_quality.bat/sh`，修改 pylint 检查路径

## ⚙️ 配置说明

### pyproject.toml

需要修改的配置项：

1. **known_first_party** (isort 配置)
   ```toml
   known_first_party = ["your_module1", "your_module2"]
   ```
   改为你的项目模块名，例如：`["handlers", "utils", "models"]`

2. **mypy.overrides** (mypy 配置)
   ```toml
   module = [
       "third_party_lib1.*",
       "third_party_lib2.*",
   ]
   ```
   改为你的项目使用的第三方库，例如：`["telegram.*", "django.*"]`

### check_code_quality.bat/sh

需要修改的配置项：

```bash
# 当前（模板）
pylint . --exit-zero

# 改为你的项目路径
pylint src/ tests/ --exit-zero
# 或
pylint your_module1/ your_module2/ --exit-zero
```

## 📝 使用说明

### 运行代码检查

**Windows:**
```bash
check_code_quality.bat
```

**Linux/Mac:**
```bash
./check_code_quality.sh
```

### 单独运行某个工具

```bash
# 格式化代码
black .

# 检查导入顺序
isort --check-only .

# 代码风格检查
flake8 .

# 代码质量检查
pylint your_module/

# 类型检查
mypy .

# 安全检查
bandit -r .

# 复杂度检查
radon cc .
```

## 🔧 自定义配置

### 调整代码风格规则

编辑 `pyproject.toml`：

```toml
[tool.black]
line-length = 100  # 修改行长度限制

[tool.pylint.messages_control]
disable = [
    "C0111",  # 添加要禁用的规则
]
```

### 添加更多工具

编辑 `requirements-dev.txt`，取消注释或添加：

```txt
# 测试框架
pytest>=7.4.0
pytest-cov>=4.1.0

# 死代码检测
vulture>=2.10

# 文档检查
pydocstyle>=6.3.0
```

## 📊 检查报告

检查完成后，会生成以下报告：

- `bandit-report.json` - 安全检查报告（JSON 格式）

可以添加更多报告生成：

```bash
# HTML 报告
pylint --output-format=html your_module/ > pylint-report.html
bandit -r . -f html -o bandit-report.html
```

## 🎯 最佳实践

1. **提交前检查**：在提交代码前运行检查脚本
2. **CI/CD 集成**：将检查脚本集成到 CI/CD 流程
3. **逐步启用**：可以先启用部分工具，逐步完善
4. **团队统一**：确保团队成员使用相同的配置

## 🔄 更新工具

定期更新工具版本：

```bash
pip install --upgrade -r requirements-dev.txt
```

## 📚 相关文档

- [Black 文档](https://black.readthedocs.io/)
- [Pylint 文档](https://pylint.readthedocs.io/)
- [MyPy 文档](https://mypy.readthedocs.io/)
- [Bandit 文档](https://bandit.readthedocs.io/)
- [Flake8 文档](https://flake8.pycqa.org/)

## ❓ 常见问题

### Q: 如何跳过某些文件的检查？

A: 在配置文件中添加排除规则：

```toml
[tool.black]
extend-exclude = '''
/(
  migrations/
  | generated/
)/
'''
```

### Q: 如何调整检查严格程度？

A: 编辑 `pyproject.toml`，修改 pylint 的 disable 列表，或调整 mypy 的检查选项。

### Q: 检查太慢怎么办？

A: 可以：
1. 只检查修改的文件
2. 使用 `--exit-zero` 选项（pylint）
3. 在 CI/CD 中并行运行检查

## 📄 许可证

此模板可自由使用和修改。


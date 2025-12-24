# 代码质量工具适配指南

本文档详细说明如何将代码质量检查工具模板适配到你的项目中。

## 📋 适配检查清单

- [ ] 复制模板文件到项目
- [ ] 安装开发工具依赖
- [ ] 配置项目模块名（known_first_party）
- [ ] 配置第三方库（mypy.overrides）
- [ ] 配置检查路径（pylint）
- [ ] 运行首次检查
- [ ] 根据结果调整配置

## 🔍 详细步骤

### 步骤 1: 识别项目结构

首先，了解你的项目结构：

```bash
# 查看项目目录结构
tree -L 2  # Linux/Mac
# 或
dir /s /b  # Windows
```

常见的 Python 项目结构：

```
project/
├── src/              # 源代码目录
│   ├── module1/
│   └── module2/
├── app/              # 应用目录
│   ├── handlers/
│   └── utils/
├── project_name/     # 包目录
│   ├── __init__.py
│   └── modules/
└── tests/            # 测试目录
```

### 步骤 2: 配置 known_first_party

在 `pyproject.toml` 中找到：

```toml
[tool.isort]
known_first_party = ["your_module1", "your_module2"]
```

**如何确定你的模块名？**

1. 查找包含 `__init__.py` 的目录
2. 这些目录通常是你的第一方模块
3. 例如：`["handlers", "callbacks", "utils", "scripts"]`

**示例：**

```toml
# Django 项目
known_first_party = ["myapp", "accounts", "blog"]

# Flask 项目
known_first_party = ["app", "models", "views"]

# 包项目
known_first_party = ["mypackage", "mypackage.submodule"]
```

### 步骤 3: 配置 mypy.overrides

在 `pyproject.toml` 中找到：

```toml
[[tool.mypy.overrides]]
module = [
    "third_party_lib1.*",
    "third_party_lib2.*",
]
ignore_missing_imports = true
```

**如何确定第三方库？**

1. 查看 `requirements.txt` 或 `setup.py`
2. 找出没有类型提示的第三方库
3. 常见需要忽略的库：
   - `telegram.*` - python-telegram-bot
   - `django.*` - Django
   - `flask.*` - Flask
   - `requests.*` - requests
   - `pandas.*` - pandas
   - `numpy.*` - numpy

**示例：**

```toml
# Telegram Bot 项目
module = ["telegram.*", "apscheduler.*"]

# Django 项目
module = ["django.*", "django_extensions.*"]

# 数据科学项目
module = ["pandas.*", "numpy.*", "matplotlib.*"]
```

### 步骤 4: 配置 pylint 检查路径

在 `check_code_quality.bat/sh` 中找到：

```bash
pylint . --exit-zero
```

**如何确定检查路径？**

1. **整个项目**：使用 `.`
   ```bash
   pylint . --exit-zero
   ```

2. **特定目录**：列出目录
   ```bash
   pylint src/ tests/ --exit-zero
   ```

3. **排除某些目录**：使用 `--ignore`
   ```bash
   pylint . --ignore=migrations,venv --exit-zero
   ```

**示例：**

```bash
# Django 项目
pylint myapp/ accounts/ --exit-zero

# Flask 项目
pylint app/ tests/ --exit-zero

# 包项目
pylint mypackage/ --exit-zero
```

### 步骤 5: 调整其他配置（可选）

#### 修改行长度限制

```toml
[tool.black]
line-length = 100  # 改为 88, 120 等

[tool.flake8]
max-line-length = 100  # 保持一致
```

#### 禁用特定规则

```toml
[tool.pylint.messages_control]
disable = [
    "C0111",  # missing-docstring
    "C0103",  # invalid-name
    # 添加更多要禁用的规则
]
```

#### 调整复杂度阈值

```bash
# 在 check_code_quality.bat/sh 中
radon cc . --min B  # B=低, C=中, D=高, E=极高
```

### 步骤 6: 运行首次检查

```bash
# Windows
check_code_quality.bat

# Linux/Mac
./check_code_quality.sh
```

### 步骤 7: 根据结果调整

检查完成后，根据输出调整配置：

1. **错误太多？**
   - 逐步启用工具
   - 调整规则严格程度
   - 禁用不相关的规则

2. **检查太慢？**
   - 只检查修改的文件
   - 使用缓存
   - 并行运行检查

3. **误报太多？**
   - 添加排除规则
   - 调整规则配置
   - 使用 `# noqa` 注释

## 🎯 项目类型特定配置

### Django 项目

```toml
[tool.isort]
known_first_party = ["myapp", "accounts", "blog"]

[[tool.mypy.overrides]]
module = ["django.*", "django_extensions.*"]
ignore_missing_imports = true

[tool.pylint.messages_control]
disable = [
    "C0111",
    "C0103",
    "R0903",
    "DJANGO_SETTINGS_MODULE",  # Django 特定
]
```

```bash
# check_code_quality.sh
pylint myapp/ accounts/ --exit-zero
```

### Flask 项目

```toml
[tool.isort]
known_first_party = ["app", "models", "views", "utils"]

[[tool.mypy.overrides]]
module = ["flask.*", "werkzeug.*"]
ignore_missing_imports = true
```

```bash
# check_code_quality.sh
pylint app/ --exit-zero
```

### FastAPI 项目

```toml
[tool.isort]
known_first_party = ["app", "api", "models", "schemas"]

[[tool.mypy.overrides]]
module = ["fastapi.*", "pydantic.*", "starlette.*"]
ignore_missing_imports = true
```

### 数据科学项目

```toml
[tool.isort]
known_first_party = ["src", "notebooks"]

[[tool.mypy.overrides]]
module = ["pandas.*", "numpy.*", "matplotlib.*", "sklearn.*"]
ignore_missing_imports = true
```

## 🔧 高级配置

### 添加 Pre-commit Hooks

创建 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

安装：
```bash
pip install pre-commit
pre-commit install
```

### CI/CD 集成

**GitHub Actions 示例：**

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: ./check_code_quality.sh
```

## 📊 检查结果解读

### Black 输出

```
All done! ✨ 🍰 ✨
X files would be reformatted.
```

- 如果有文件需要格式化，运行 `black .` 自动格式化

### Flake8 输出

```
file.py:10:1: F401 'module' imported but unused
```

- `F401`: 未使用的导入
- `E501`: 行太长
- `W503`: 行尾运算符

### Pylint 输出

```
file.py:10:0: C0111: Missing module docstring
```

- `C`: 约定（Convention）
- `R`: 重构（Refactor）
- `W`: 警告（Warning）
- `E`: 错误（Error）

### MyPy 输出

```
file.py:10: error: Function is missing a type annotation
```

- 添加类型注解可以解决大部分问题

## ✅ 验证配置

运行以下命令验证配置是否正确：

```bash
# 测试 Black
black --check .

# 测试 isort
isort --check-only .

# 测试 flake8
flake8 .

# 测试 pylint（只检查一个文件）
pylint your_module/__init__.py

# 测试 mypy
mypy your_module/__init__.py
```

## 🎓 学习资源

- [Python 代码风格指南 (PEP 8)](https://pep8.org/)
- [类型提示 (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Black 代码风格](https://black.readthedocs.io/en/stable/the_black_code_style.html)

## 💡 提示

1. **逐步启用**：不要一次性启用所有工具，逐步添加
2. **团队协作**：确保团队成员使用相同的配置
3. **定期更新**：定期更新工具版本
4. **自定义规则**：根据项目特点调整规则
5. **文档化**：记录项目的代码风格约定


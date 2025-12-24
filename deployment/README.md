# 进程管理配置说明

本目录包含用于管理 Loan Bot 机器人进程的配置文件。

## 📋 目录结构

```
deployment/
├── loan-bot.service          # systemd 服务配置文件
├── supervisor.conf           # Supervisor 配置文件
├── install-systemd.sh        # systemd 安装脚本
├── install-supervisor.sh     # Supervisor 安装脚本
├── windows-service-install.bat # Windows Service 安装脚本
└── README.md                 # 本文件
```

---

## 🐧 Linux/Unix 系统

### 方案一：systemd（推荐）

**适用系统**: Ubuntu 18.04+, Debian 9+, CentOS 7+, RHEL 7+

#### 安装步骤

1. **复制服务文件**:
   ```bash
   sudo cp deployment/loan-bot.service /etc/systemd/system/
   ```

2. **编辑服务文件**，设置环境变量:
   ```bash
   sudo nano /etc/systemd/system/loan-bot.service
   ```
   
   修改以下环境变量：
   ```ini
   Environment="BOT_TOKEN=your_bot_token_here"
   Environment="ADMIN_USER_IDS=your_admin_ids_here"
   Environment="DATA_DIR=/data"
   Environment="DEBUG=0"
   ```
   
   修改工作目录和 Python 路径：
   ```ini
   WorkingDirectory=/path/to/your/project
   ExecStart=/usr/bin/python3 /path/to/your/project/main.py
   ```

3. **重新加载 systemd**:
   ```bash
   sudo systemctl daemon-reload
   ```

4. **启用服务**（开机自启）:
   ```bash
   sudo systemctl enable loan-bot.service
   ```

5. **启动服务**:
   ```bash
   sudo systemctl start loan-bot.service
   ```

#### 使用安装脚本（推荐）

```bash
cd deployment
chmod +x install-systemd.sh
sudo ./install-systemd.sh
```

脚本会自动：
- 复制服务文件
- 更新路径配置
- 提示编辑环境变量
- 启用服务

#### 常用命令

```bash
# 启动服务
sudo systemctl start loan-bot

# 停止服务
sudo systemctl stop loan-bot

# 重启服务
sudo systemctl restart loan-bot

# 查看状态
sudo systemctl status loan-bot

# 查看日志（实时）
sudo journalctl -u loan-bot -f

# 查看最近100行日志
sudo journalctl -u loan-bot -n 100

# 查看错误日志
sudo journalctl -u loan-bot -p err

# 禁用开机自启
sudo systemctl disable loan-bot

# 启用开机自启
sudo systemctl enable loan-bot
```

---

### 方案二：Supervisor

**适用系统**: 所有 Linux 系统

#### 安装 Supervisor

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install supervisor
```

**CentOS/RHEL**:
```bash
sudo yum install supervisor
# 或
sudo dnf install supervisor
```

#### 安装步骤

1. **复制配置文件**:
   ```bash
   sudo cp deployment/supervisor.conf /etc/supervisor/conf.d/loan-bot.conf
   ```

2. **编辑配置文件**，设置环境变量和路径:
   ```bash
   sudo nano /etc/supervisor/conf.d/loan-bot.conf
   ```
   
   修改以下内容：
   ```ini
   command=/usr/bin/python3 /path/to/your/project/main.py
   directory=/path/to/your/project
   environment=BOT_TOKEN="your_bot_token",ADMIN_USER_IDS="your_admin_ids",DATA_DIR="/data",DEBUG="0"
   ```

3. **创建日志目录**:
   ```bash
   sudo mkdir -p /var/log/loan-bot
   sudo chmod 755 /var/log/loan-bot
   ```

4. **重新加载配置**:
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

#### 使用安装脚本（推荐）

```bash
cd deployment
chmod +x install-supervisor.sh
sudo ./install-supervisor.sh
```

#### 常用命令

```bash
# 启动服务
sudo supervisorctl start loan-bot

# 停止服务
sudo supervisorctl stop loan-bot

# 重启服务
sudo supervisorctl restart loan-bot

# 查看状态
sudo supervisorctl status loan-bot

# 查看所有服务状态
sudo supervisorctl status

# 查看日志（实时）
tail -f /var/log/loan-bot/loan-bot.log

# 查看错误日志
tail -f /var/log/loan-bot/loan-bot-error.log

# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update
```

---

## 🪟 Windows 系统

### 方案：Windows Service（使用 NSSM）

**NSSM (Non-Sucking Service Manager)** 是一个 Windows 服务管理工具。

#### 安装 NSSM

1. **下载 NSSM**:
   - 访问: https://nssm.cc/download
   - 下载最新版本（推荐 64位）

2. **解压并添加到 PATH**:
   - 解压到 `C:\nssm`
   - 将 `C:\nssm\win64` 添加到系统 PATH 环境变量

3. **验证安装**:
   ```cmd
   nssm version
   ```

#### 安装步骤

1. **创建日志目录**:
   ```cmd
   mkdir logs
   ```

2. **运行安装脚本**:
   ```cmd
   cd deployment
   windows-service-install.bat
   ```

   或手动安装：
   ```cmd
   nssm install LoanBot python "C:\path\to\your\project\main.py"
   nssm set LoanBot AppDirectory "C:\path\to\your\project"
   nssm set LoanBot AppStdout "C:\path\to\your\project\logs\loan-bot.log"
   nssm set LoanBot AppStderr "C:\path\to\your\project\logs\loan-bot-error.log"
   nssm set LoanBot Start SERVICE_AUTO_START
   ```

3. **设置环境变量**（在系统环境变量中设置）:
   - `BOT_TOKEN`: Telegram Bot Token
   - `ADMIN_USER_IDS`: 管理员用户ID列表（逗号分隔）
   - `DATA_DIR`: 数据目录路径（可选）
   - `DEBUG`: 调试模式（可选，默认 0）

4. **启动服务**:
   ```cmd
   nssm start LoanBot
   ```

#### 常用命令

```cmd
# 启动服务
nssm start LoanBot

# 停止服务
nssm stop LoanBot

# 重启服务
nssm restart LoanBot

# 查看状态
nssm status LoanBot

# 编辑服务配置
nssm edit LoanBot

# 删除服务
nssm remove LoanBot confirm

# 查看日志
type logs\loan-bot.log
```

#### 使用 Windows 服务管理器

1. 按 `Win + R`，输入 `services.msc`
2. 找到 `LoanBot` 服务
3. 右键可以启动、停止、重启服务
4. 双击可以查看服务属性

---

## 🔧 环境变量配置

所有方案都需要设置以下环境变量：

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `BOT_TOKEN` | ✅ | Telegram Bot Token | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ADMIN_USER_IDS` | ✅ | 管理员用户ID列表（逗号分隔） | `123456789,987654321` |
| `DATA_DIR` | ❌ | 数据目录路径 | `/data` 或 `C:\data` |
| `DEBUG` | ❌ | 调试模式（0=关闭，1=开启） | `0` |

---

## 📝 日志管理

### systemd

日志自动记录到 systemd journal：
```bash
# 查看实时日志
sudo journalctl -u loan-bot -f

# 查看最近100行
sudo journalctl -u loan-bot -n 100

# 查看今天的日志
sudo journalctl -u loan-bot --since today

# 查看错误日志
sudo journalctl -u loan-bot -p err
```

### Supervisor

日志文件位置：
- 标准输出: `/var/log/loan-bot/loan-bot.log`
- 错误输出: `/var/log/loan-bot/loan-bot-error.log`

日志自动轮转（保留5个备份，每个最大10MB）

### Windows Service (NSSM)

日志文件位置：
- 标准输出: `项目目录\logs\loan-bot.log`
- 错误输出: `项目目录\logs\loan-bot-error.log`

日志自动轮转（每天轮转，每个最大10MB）

---

## 🚨 故障排查

### 服务无法启动

1. **检查环境变量**:
   ```bash
   # systemd
   sudo systemctl show loan-bot | grep Environment
   
   # Supervisor
   sudo supervisorctl status loan-bot
   ```

2. **查看日志**:
   ```bash
   # systemd
   sudo journalctl -u loan-bot -n 50
   
   # Supervisor
   tail -n 50 /var/log/loan-bot/loan-bot-error.log
   ```

3. **检查 Python 路径**:
   ```bash
   which python3
   # 或
   python3 --version
   ```

4. **检查文件权限**:
   ```bash
   ls -la /path/to/your/project/main.py
   ```

### 服务频繁重启

1. **查看错误日志**，找出崩溃原因
2. **检查资源限制**（内存、文件描述符）
3. **检查数据库连接**
4. **检查网络连接**

---

## 🔄 更新服务

### systemd

```bash
# 停止服务
sudo systemctl stop loan-bot

# 更新代码
cd /path/to/your/project
git pull  # 或其他更新方式

# 重启服务
sudo systemctl start loan-bot
```

### Supervisor

```bash
# 停止服务
sudo supervisorctl stop loan-bot

# 更新代码
cd /path/to/your/project
git pull  # 或其他更新方式

# 重启服务
sudo supervisorctl start loan-bot
```

### Windows Service

```cmd
# 停止服务
nssm stop LoanBot

# 更新代码
cd C:\path\to\your\project
git pull  # 或其他更新方式

# 启动服务
nssm start LoanBot
```

---

## 📚 更多信息

- **systemd**: https://www.freedesktop.org/software/systemd/man/systemd.service.html
- **Supervisor**: http://supervisord.org/
- **NSSM**: https://nssm.cc/

---

## ✅ 推荐方案

- **Linux 生产环境**: systemd（系统集成，日志管理方便）
- **Linux 开发环境**: Supervisor（配置灵活，易于调试）
- **Windows 环境**: NSSM（简单易用，功能完善）


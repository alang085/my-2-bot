"""检查部署准备情况的脚本"""
import os
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

print("=" * 60)
print("部署准备检查")
print("=" * 60)

project_root = Path(__file__).parent.absolute()

# 检查关键文件
print("\n1. 检查关键文件:")
key_files = {
    'Dockerfile': 'Docker 构建文件',
    'zeabur.json': 'Zeabur 配置文件',
    'requirements.txt': 'Python 依赖文件',
    'runtime.txt': 'Python 版本文件',
    'Procfile': '启动命令文件',
    'main.py': '主程序文件'
}

all_ready = True
for file_name, description in key_files.items():
    file_path = project_root / file_name
    exists = file_path.exists()
    status = "✓" if exists else "✗"
    print(f"   {status} {file_name} - {description}")
    if not exists:
        all_ready = False

# 检查 Dockerfile 内容
print("\n2. 检查 Dockerfile 内容:")
if (project_root / 'Dockerfile').exists():
    with open(project_root / 'Dockerfile', 'r', encoding='utf-8') as f:
        dockerfile_content = f.read()
        if 'FROM python' in dockerfile_content:
            print("   ✓ 包含 Python 基础镜像")
        else:
            print("   ✗ 缺少 Python 基础镜像")
            all_ready = False
        
        if 'COPY requirements.txt' in dockerfile_content:
            print("   ✓ 包含复制 requirements.txt")
        else:
            print("   ✗ 缺少复制 requirements.txt")
            all_ready = False
        
        if 'pip install' in dockerfile_content:
            print("   ✓ 包含 pip install 命令")
        else:
            print("   ✗ 缺少 pip install 命令")
            all_ready = False
        
        if 'CMD' in dockerfile_content or 'ENTRYPOINT' in dockerfile_content:
            print("   ✓ 包含启动命令")
        else:
            print("   ✗ 缺少启动命令")
            all_ready = False

# 检查 zeabur.json
print("\n3. 检查 zeabur.json 配置:")
if (project_root / 'zeabur.json').exists():
    import json
    try:
        with open(project_root / 'zeabur.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            builder = config.get('build', {}).get('builder', '')
            if builder == 'DOCKER':
                print("   ✓ 构建器设置为 DOCKER")
            else:
                print(f"   ⚠ 构建器设置为 {builder}（应该是 DOCKER）")
            
            start_cmd = config.get('deploy', {}).get('startCommand', '')
            if start_cmd:
                print(f"   ✓ 启动命令: {start_cmd}")
            else:
                print("   ⚠ 未设置启动命令")
    except Exception as e:
        print(f"   ✗ 解析 zeabur.json 失败: {e}")
        all_ready = False

# 检查 requirements.txt
print("\n4. 检查 requirements.txt:")
if (project_root / 'requirements.txt').exists():
    with open(project_root / 'requirements.txt', 'r', encoding='utf-8') as f:
        requirements = f.read()
        if 'python-telegram-bot' in requirements:
            print("   ✓ 包含 python-telegram-bot")
        else:
            print("   ✗ 缺少 python-telegram-bot")
            all_ready = False

# 总结
print("\n" + "=" * 60)
if all_ready:
    print("✅ 所有检查通过！可以开始部署。")
    print("\n下一步操作：")
    print("1. 登录 Zeabur 平台")
    print("2. 进入项目设置")
    print("3. 清除构建缓存")
    print("4. 检查构建器设置为 DOCKER")
    print("5. 检查环境变量（BOT_TOKEN, ADMIN_USER_IDS）")
    print("6. 重新部署")
    print("\n详细步骤请查看：Zeabur部署操作步骤.md")
else:
    print("❌ 检查未通过，请修复上述问题后再部署。")
print("=" * 60)


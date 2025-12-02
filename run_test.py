"""快速运行测试脚本"""
import sys
import subprocess
from pathlib import Path

print("=" * 80)
print("运行测试脚本")
print("=" * 80)
print()

# 运行数据完整性检查
print("1. 运行数据完整性检查...")
print("-" * 80)
result1 = subprocess.run([sys.executable, "test_data_integrity.py"], 
                        capture_output=True, text=True)
print(result1.stdout)
if result1.stderr:
    print("错误输出:", result1.stderr)
print()

# 运行完整测试
print("2. 运行完整功能测试...")
print("-" * 80)
result2 = subprocess.run([sys.executable, "test_complete_local.py"], 
                        capture_output=True, text=True)
print(result2.stdout)
if result2.stderr:
    print("错误输出:", result2.stderr)
print()

print("=" * 80)
print("测试完成")
print("=" * 80)


#!/usr/bin/env python3
"""
测试运行脚本
使用方法：
python run_tests.py
"""

import subprocess
import sys
import os

def run_tests():
    """运行所有测试"""
    print("开始运行测试...")
    
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    
    try:
        # 运行pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_main.py", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        print("测试输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ 所有测试通过!")
        else:
            print(f"\n❌ 测试失败，退出码: {result.returncode}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 
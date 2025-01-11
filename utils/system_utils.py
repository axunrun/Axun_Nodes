"""
系统工具函数
提供系统级别的依赖安装和配置功能
"""

import importlib.util
import sys
import platform
import subprocess
import logging

def install_tkinter():
    """
    安装tkinter系统依赖
    
    引用:
    - nodes/Qtools/dir_picker.py: 用于目录选择对话框
    
    功能:
    - 检查tkinter是否已安装
    - 根据不同操作系统安装tkinter
    - 支持MacOS(brew)、Linux(apt)和Windows(pip)
    """
    try:
        importlib.import_module('tkinter')
    except ImportError:
        print("[AxunNodes] 正在尝试安装tkinter")
        try:
            system = platform.system()
            if system == 'Darwin':
                result = subprocess.run(['brew', 'install', 'python-tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Brew安装失败，请确保已安装brew (https://brew.sh/)")
            elif system == 'Linux':
                result = subprocess.run(['sudo', 'apt', '-y', 'install', 'python3-tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Apt安装失败")
            else:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Pip安装失败")
        except Exception as e:
            print("[AxunNodes] 无法安装tkinter，请尝试设置TCL_LIBRARY和TK_LIBRARY环境变量")
            print(e)

def setup_logging():
    """
    配置日志系统
    
    引用:
    - 全局使用
    - nodes/Qtools/*: 用于日志输出
    - nodes/Translator/*: 用于日志输出
    - nodes/Lotus/*: 用于日志输出
    
    功能:
    - 配置全局日志格式
    - 设置日志级别
    - 统一日志输出样式
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ) 
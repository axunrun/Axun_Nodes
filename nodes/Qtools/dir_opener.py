"""
Directory Opener Node for ComfyUI
提供一键打开目录的功能节点
"""

import os
import platform
import subprocess
from server import PromptServer
from aiohttp import web

# 添加API路由用于打开目录
@PromptServer.instance.routes.get("/axun-dir/open-directory")
async def open_directory_handler(request):
    """处理打开目录的请求"""
    try:
        directory = request.query.get("directory", "")
        if not directory:
            return web.Response(status=400, text="目录路径为空")
            
        # 转换路径格式
        directory = directory.replace('/', '\\') if platform.system() == "Windows" else directory
        
        if not os.path.exists(directory):
            return web.Response(status=400, text=f"目录不存在: {directory}")
            
        print(f"[DirOpener] 尝试打开目录: {directory}")
            
        # 根据操作系统选择打开方式
        system = platform.system()
        if system == "Windows":
            # 直接打开目录
            subprocess.run(['explorer', directory])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", directory])
        else:  # Linux
            subprocess.run(["xdg-open", directory])
            
        print(f"[DirOpener] 成功打开目录: {directory}")
        return web.Response(text="success")
    except Exception as e:
        print(f"[DirOpener] 打开目录失败: {str(e)}")
        return web.Response(status=500, text=str(e))

class DirOpener:
    """目录打开器节点"""
    
    def __init__(self):
        self.output_dir = ""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_dir": ("STRING", {"default": "", "multiline": False}),
                "story_dir": ("STRING", {"default": "", "multiline": False}),
                "cover_dir": ("STRING", {"default": "", "multiline": False}),
                "animation_dir": ("STRING", {"default": "", "multiline": False}),
                "other_dir": ("STRING", {"default": "", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "open_directory"
    CATEGORY = "!Axun Nodes/Queue Tools"
    OUTPUT_NODE = True

    def open_directory(self, character_dir: str, story_dir: str, cover_dir: str, animation_dir: str, other_dir: str):
        """打开目录"""
        # 验证所有目录
        for dir_path in [character_dir, story_dir, cover_dir, animation_dir, other_dir]:
            if dir_path:
                dir_path = dir_path.replace('/', '\\') if platform.system() == "Windows" else dir_path
                if not os.path.exists(dir_path):
                    print(f"[DirOpener] 目录不存在: {dir_path}")
        return ()
    
    @classmethod
    def VALIDATE_INPUTS(cls, character_dir: str, story_dir: str, cover_dir: str, animation_dir: str, other_dir: str):
        """验证输入"""
        # 允许目录为空
        for dir_path in [character_dir, story_dir, cover_dir, animation_dir, other_dir]:
            if dir_path:
                dir_path = dir_path.replace('/', '\\') if platform.system() == "Windows" else dir_path
                if not os.path.exists(dir_path):
                    return False
        return True 
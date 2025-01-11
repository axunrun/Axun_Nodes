from typing import Tuple, Dict, Any
import logging
import tkinter as tk
from tkinter import filedialog
import os
import json
from aiohttp import web
import server
from folder_paths import get_input_directory

# 配置日志
logger = logging.getLogger("axun_nodes.dir_picker")

# 全局变量
picked_dirs = {}
current_path = os.path.dirname(os.path.abspath(__file__))

def save_picked_dirs():
    """保存已选择的目录"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "dir_picker.json")
        with open(config_path, 'w') as f:
            json.dump(picked_dirs, f)
    except Exception as e:
        logger.error(f"保存目录失败: {str(e)}")

def load_picked_dirs():
    """加载已保存的目录"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "dir_picker.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                picked_dirs.update(json.load(f))
    except Exception as e:
        logger.error(f"加载目录失败: {str(e)}")

class DirPicker:
    """
    目录选择器节点
    功能：
    1. 目录选择按钮
    2. 路径保存
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "directory": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("directory",)
    FUNCTION = "pick_directory"
    CATEGORY = "!Axun Nodes/Queue Tools"
    OUTPUT_NODE = True

    def __init__(self):
        load_picked_dirs()

    def pick_directory(self, directory: str, prompt=None, id=None) -> Tuple[str]:
        """
        选择目录
        
        Args:
            directory: 目录路径
            prompt: 提示信息
            id: 节点ID
            
        Returns:
            Tuple[str]: 选择的目录路径
        """
        try:
            # 从缓存获取目录
            if id and id in picked_dirs:
                directory = picked_dirs[id]
            return (directory,)
        except Exception as e:
            logger.error(f"目录选择失败: {str(e)}")
            return (directory,)

    @classmethod
    async def select_directory(cls, request):
        """处理目录选择请求"""
        try:
            node_id = request.rel_url.query.get('id', '')
            folder_path = cls._select_folder(node_id)
            if folder_path:
                picked_dirs[node_id] = folder_path
                save_picked_dirs()
                
            # 发送节点更新事件
            server.PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "directory",
                    "type": "string",
                    "value": folder_path
                }
            )
            return web.json_response({'folder': folder_path})
        except Exception as e:
            logger.error(f"处理目录选择请求失败: {str(e)}")
            return web.json_response({'folder': ''})

    @staticmethod
    def _select_folder(node_id: str) -> str:
        """打开目录选择对话框"""
        try:
            # 获取初始目录
            default_path = picked_dirs.get(node_id) or get_input_directory()
            
            # 创建Tk窗口
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', True)
            
            # 打开目录选择对话框
            folder_path = filedialog.askdirectory(
                initialdir=default_path,
                title="选择目录"
            )
            
            # 清理对话框状态
            filedialog.dialogstates = {}
            root.destroy()
            
            logger.info(f"选择目录: {folder_path}")
            return folder_path or default_path
            
        except Exception as e:
            logger.error(f"选择目录失败: {str(e)}")
            return ""

# 注册API路由
@server.PromptServer.instance.routes.get("/axun-dir/select-directory")
async def select_directory_route(request):
    """目录选择路由"""
    return await DirPicker.select_directory(request)

@server.PromptServer.instance.routes.get("/axun-dir/get-directory") 
async def get_directory_route(request):
    """获取已选目录路由"""
    node_id = request.rel_url.query.get('id', '')
    return web.json_response({
        'folder': picked_dirs.get(node_id, ''),
    })

# API路由映射
dir_api = {
    "select_directory": select_directory_route,
    "get_directory": get_directory_route
} 
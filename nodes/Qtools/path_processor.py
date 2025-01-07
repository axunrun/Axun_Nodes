import os
import torch
import numpy as np
from PIL import Image, ImageOps
import re
import random
import logging
from server import PromptServer
from aiohttp import web

# 配置日志
logger = logging.getLogger("axun_nodes.path_processor")

# 全局变量
loop_indexes = {}

class PathProcessor:
    """
    路径处理节点
    功能：
    1. 支持批量/单文件模式切换
    2. 文件过滤（扩展名/正则表达式）
    3. 文件排序（名称/修改时间/创建时间）
    4. 自动索引管理
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "load_path": ("STRING", {"forceInput": True, "default": ""}),
                "save_path": ("STRING", {"forceInput": True, "default": ""}),
                "filter_type": (["regex", "extension"], {"default": "extension"}),
                "filter_value": ("STRING", {"default": ""}),
                "sort_by": (["name", "date_modified", "date_created"], {"default": "name"}),
                "sort_order": (["asc", "desc", "random"], {"default": "asc"}),
                "path_mode": ("BOOLEAN", {"default": True, "label_on": "批量模式", "label_off": "单次模式"}),
                "single_image": ("IMAGE",),
                "single_mask": ("MASK",),
                "loop_index": ("INT", {"default": 0, "min": 0, "max": 999999, "step": 1}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING", "STRING", "IMAGE", "MASK")
    RETURN_NAMES = ("file_count", "current_index", "filename", "filepath", "image", "mask")
    FUNCTION = "process_path"
    CATEGORY = "!Axun Nodes/Queue Tools"
    OUTPUT_NODE = True

    def process_path(self, load_path, save_path, filter_type, filter_value, sort_by, sort_order, path_mode, single_image, single_mask, loop_index, prompt, id):
        try:
            # 单文件模式直接返回
            if not path_mode:
                return (0, 0, "Single_File", f"{save_path}/Single", single_image, single_mask)

            # 验证路径
            if not load_path or not save_path:
                logger.error("路径不能为空")
                return (0, 0, "", "", torch.zeros((1, 3, 64, 64)), torch.zeros((64, 64)))

            # 获取匹配文件
            matched_files = self._filter_files(load_path, filter_type, filter_value, sort_by, sort_order)
            file_count = len(matched_files)
            
            if file_count == 0:
                loop_indexes[id] = 0
                self._update_index(id, 0)
                logger.warning(f"在目录中未找到文件: {load_path}")
                return (0, 0, "", "", torch.zeros((1, 3, 64, 64)), torch.zeros((64, 64)))
            
            # 获取当前索引，优先使用手动设置的值
            current_index = loop_index if loop_index is not None else loop_indexes.get(id, 0)
            
            # 确保索引在有效范围内并获取当前文件
            current_index = current_index % file_count
            current_file = matched_files[current_index]
            current_file_path = os.path.join(load_path, current_file)
            
            # 构建输出路径
            batch_file = os.path.splitext(current_file)[0]
            current_dir = os.path.basename(load_path)
            batch_directory = f"{save_path}/{current_dir}"
            
            # 加载图像和mask
            image = self._load_image(current_file_path)
            if image is None:
                logger.error(f"图像加载失败: {current_file_path}")
                return (0, 0, "", "", torch.zeros((1, 3, 64, 64)), torch.zeros((64, 64)))
            
            mask = self._load_mask(current_file_path)
            
            # 准备输出并更新下一个索引
            output = (file_count, current_index, batch_file, batch_directory, image, mask)
            next_index = (current_index + 1) % file_count
            
            # 更新全局状态和前端显示
            loop_indexes[id] = next_index
            self._update_index(id, next_index)
            
            return output
                
        except Exception as e:
            logger.error(f"路径处理失败: {str(e)}")
            return (0, 0, "", "", torch.zeros((1, 3, 64, 64)), torch.zeros((64, 64)))

    def _filter_files(self, directory, filter_type, filter_value, sort_by, sort_order):
        try:
            files = os.listdir(directory)
            matched_files = []
            
            # 排序
            if sort_by == "name":
                files.sort()
            elif sort_by == "date_modified":
                files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)))
            elif sort_by == "date_created":
                files.sort(key=lambda x: os.path.getctime(os.path.join(directory, x)))
            
            # 排序顺序
            if sort_order == "desc":
                files.reverse()
            elif sort_order == "random":
                random.shuffle(files)
            
            # 过滤
            for file in files:
                try:
                    if filter_type == "regex" and re.match(filter_value, file):
                        matched_files.append(file)
                    elif filter_type == "extension" and file.endswith(filter_value):
                        matched_files.append(file)
                except re.error as e:
                    logger.error(f"正则表达式错误: {str(e)}")
                    continue
                    
            return matched_files
            
        except Exception as e:
            logger.error(f"文件过滤失败: {str(e)}")
            return []

    def _load_image(self, file_path):
        try:
            i = Image.open(file_path)
            i = ImageOps.exif_transpose(i)
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            return torch.from_numpy(image)[None,]
        except Exception as e:
            logger.error(f"图像加载失败 '{file_path}': {str(e)}")
            return None

    def _load_mask(self, file_path):
        try:
            i = Image.open(file_path)
            i = ImageOps.exif_transpose(i)
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            return mask
        except Exception as e:
            logger.error(f"Mask加载失败 '{file_path}': {str(e)}")
            return torch.zeros((64, 64), dtype=torch.float32, device="cpu")

    def _update_index(self, node_id: str, index: int):
        """更新前端显示的索引值"""
        try:
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "loop_index",
                    "type": "int",
                    "value": index
                }
            )
        except Exception as e:
            logger.error(f"更新索引失败: {str(e)}")

# API路由
@PromptServer.instance.routes.get("/axun-dir/loop-index")
async def get_loop_index(request):
    node_id = request.rel_url.query.get('id', '')
    current_index = loop_indexes.get(node_id, 0)
    return web.json_response({'loop_index': current_index})

@PromptServer.instance.routes.get("/axun-dir/set-loop-index")
async def set_loop_index(request):
    node_id = request.rel_url.query.get('id', '')
    index = int(request.rel_url.query.get('index', 0))
    loop_indexes[node_id] = index
    return web.json_response({'success': True}) 
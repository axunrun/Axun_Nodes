import re
from server import PromptServer
from aiohttp import web
import json

text_indices = {}

@PromptServer.instance.routes.get("/axun-text/text-index")
async def get_text_index(request):
    """获取文本索引"""
    node_id = request.query.get("id")
    if not node_id:
        return web.Response(status=400)
    return web.json_response({"text_index": text_indices.get(node_id, 1)})

@PromptServer.instance.routes.post("/axun-text/set-text-index")
async def set_text_index(request):
    """设置文本索引"""
    node_id = request.query.get("id")
    index = request.query.get("index")
    if not node_id or not index:
        return web.Response(status=400)
    try:
        text_indices[node_id] = int(index)
        return web.Response(status=200)
    except ValueError:
        return web.Response(status=400)

class TextProcessor:
    """文本处理器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "sample_text": ("STRING", {"multiline": True}),
                "append_text": ("STRING", {"multiline": True, "default": ""}),
                "content_type": ("STRING", {"default": "page_*_image_en"}),
                "prefix": ("STRING", {"default": ""}),
                "suffix": ("STRING", {"default": ""}),
                "text_index": ("INT", {"default": 1, "min": 1, "max": 999999}),
            },
            "hidden": {
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("combined_text", "current_index")
    FUNCTION = "process_text"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def process_text(self, sample_text: str, append_text: str, content_type: str, prefix: str, suffix: str, text_index: int, id: str):
        """处理文本内容"""
        # 提取指定格式的内容
        pattern = f'"{content_type.replace("*", "\\d+")}":\\s*"([^"]*)"'
        matches = re.finditer(pattern, sample_text)
        texts = []
        for match in matches:
            if match.group(1):  # 获取匹配的内容
                texts.append(match.group(1).strip())
        
        if not texts:
            text_indices[id] = 1
            self._update_index(id, 1)
            return "", 1
            
        # 获取当前索引，优先使用手动设置的值
        current_index = text_index if text_index is not None else text_indices.get(id, 1)
        
        # 确保索引在有效范围内
        max_index = len(texts)
        current_index = ((current_index - 1) % max_index) + 1
        
        # 获取对应的文本并用前后缀包裹
        text = texts[current_index - 1] if texts else ""
        wrapped_text = f"{prefix}{text}{suffix}"
        
        # 如果有附加文本，添加到结果中
        if append_text:
            wrapped_text = f"{wrapped_text}\n{append_text}"
            
        # 计算并保存下一个索引
        next_index = current_index + 1
        if next_index > max_index:
            next_index = 1
        text_indices[id] = next_index
        self._update_index(id, next_index)
            
        return wrapped_text, current_index

    def _update_index(self, node_id: str, index: int):
        """更新前端显示的索引值"""
        try:
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "text_index",
                    "type": "int",
                    "value": index
                }
            )
        except Exception as e:
            print(f"更新索引失败: {str(e)}") 
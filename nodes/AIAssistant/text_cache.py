import os
import json
import re
from server import PromptServer
from aiohttp import web

# 用于存储文本缓存的字典
text_cache = {}

def clean_text(text: str) -> str:
    """清理文本，去除索引标记，只保留括号内的内容"""
    try:
        # 使用统一的格式处理 ##标识:{内容}
        # 可以处理：
        # ##名字:{内容}
        # ##scene_数字:{内容}
        # ##story_数字:{内容}
        pattern = r'##[^{:]*:\{(.*?)\}'
        
        # 找到所有匹配项
        matches = re.finditer(pattern, text, re.DOTALL)
        
        # 提取所有括号内的内容并用换行符连接
        result = []
        for match in matches:
            content = match.group(1).strip()
            if content:  # 只添加非空内容
                result.append(content)
        
        # 用换行符连接所有内容
        cleaned_text = '\n'.join(result)
        
        # 去除多余的空白字符，但保留换行符
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n\s+', '\n', cleaned_text)
        cleaned_text = re.sub(r'\s+\n', '\n', cleaned_text)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text.strip()
    except Exception as e:
        print(f"[TextCache] 清理文本时出错: {str(e)}")
        return text

@PromptServer.instance.routes.get("/axun-text/get-cache")
async def get_cached_text(request):
    """获取缓存的文本"""
    node_id = request.query.get("id")
    if not node_id:
        return web.Response(status=400)
    return web.json_response({"text": text_cache.get(node_id, "")})

@PromptServer.instance.routes.post("/axun-text/set-cache")
async def set_cached_text(request):
    """设置缓存的文本"""
    node_id = request.query.get("id")
    if not node_id:
        return web.Response(status=400)
    try:
        data = await request.json()
        text = data.get("text", "")
        text_cache[node_id] = text
        return web.Response(status=200)
    except Exception as e:
        print(f"[TextCache] 设置缓存失败: {str(e)}")
        return web.Response(status=400)

class TextCache:
    """带缓存的文本处理器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
            },
            "optional": {
                "input_text": ("STRING", {"multiline": True, "default": ""}),
                "cache_text": ("STRING", {"multiline": True, "default": ""}),
            },
            "hidden": {
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_text",)
    FUNCTION = "process_text"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def process_text(self, input_text: str = "", cache_text: str = "", id: str = None):
        """处理文本内容"""
        try:
            print(f"[TextCache] 开始处理文本:")
            print(f"[TextCache] - input_text: {input_text[:100] if input_text else 'None'}")
            print(f"[TextCache] - cache_text: {cache_text[:100] if cache_text else 'None'}")
            print(f"[TextCache] - id: {id}")
            
            # 如果有输入文本，使用输入文本并更新缓存
            if input_text and input_text.strip():
                print(f"[TextCache] 处理输入文本")
                # 更新缓存
                text_cache[id] = input_text
                # 更新前端显示
                self._update_cache_display(id, input_text)
                # 返回处理后的文本
                return (input_text,)
            
            # 如果没有输入文本，使用缓存文本
            elif cache_text and cache_text.strip():
                print(f"[TextCache] 使用缓存文本: {cache_text[:100]}")
                return (cache_text,)
            
            # 如果都没有，返回空字符串
            else:
                print("[TextCache] 无可用文本，返回空字符串")
                return ("",)
            
        except Exception as e:
            print(f"[TextCache] 处理文本时出错: {str(e)}")
            return ("",)

    def _update_cache_display(self, node_id: str, text: str):
        """更新前端显示的缓存文本"""
        try:
            print(f"[TextCache] 更新缓存显示: node_id={node_id}, text={text[:100]}")
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "cache_text",
                    "type": "string",
                    "value": text
                }
            )
        except Exception as e:
            print(f"[TextCache] 更新缓存显示失败: {str(e)}") 
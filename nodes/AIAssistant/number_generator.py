import random
import string
from server import PromptServer
from aiohttp import web
import json

# 存储每个节点的当前数字值
number_values = {}

@PromptServer.instance.routes.get("/axun-number/get-value")
async def get_number_value(request):
    """获取数字值"""
    node_id = request.query.get("id")
    if not node_id:
        return web.Response(status=400)
    return web.json_response({"number_value": number_values.get(node_id, 1)})

@PromptServer.instance.routes.post("/axun-number/set-value")
async def set_number_value(request):
    """设置数字值"""
    node_id = request.query.get("id")
    value = request.query.get("value")
    if not node_id or not value:
        return web.Response(status=400)
    try:
        number_values[node_id] = int(value)
        return web.Response(status=200)
    except ValueError:
        return web.Response(status=400)

class NumberGenerator:
    """数字生成器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prefix_text": ("STRING", {"default": ""}),
                "middle_text": ("STRING", {"default": ""}),
                "number_value": ("INT", {"default": 1, "min": 1}),
                "max_value": ("INT", {"default": 10, "min": 1}),
                "suffix_text": ("STRING", {"default": ""}),
            },
            "hidden": {
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def generate(self, prefix_text: str, middle_text: str, number_value: int, max_value: int, suffix_text: str, id: str):
        """生成递进数字"""
        try:
            # 获取当前数字值
            current_number = number_values.get(id, number_value)
            
            # 计算下一个数字值
            next_number = current_number + 1 if current_number < max_value else 1
            
            # 更新数值
            number_values[id] = next_number
            self._update_value(id, next_number)
            
            # 组合最终文本
            result = f"{prefix_text}{middle_text}{current_number}{suffix_text}"
            
            print(f"[NumberGenerator] 当前值: {current_number}, 下一个值: {next_number}")
            return (result,)
            
        except Exception as e:
            print(f"[NumberGenerator] 生成数字时出错: {str(e)}")
            return (f"{prefix_text}{middle_text}{number_value}{suffix_text}",)

    def _update_value(self, node_id: str, value: int):
        """更新前端显示的数字值"""
        try:
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "number_value",
                    "type": "int",
                    "value": value
                }
            )
        except Exception as e:
            print(f"[NumberGenerator] 更新数字值失败: {str(e)}") 
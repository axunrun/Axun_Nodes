import json
import asyncio
import aiohttp
from aiohttp import web
from server import PromptServer
from typing import List
import os

from .utils.api_handler import SiliconCloudHandler, DeepSeekHandler
from .utils.image_utils import encode_comfy_image

class SiliconCloudLLMAPI:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ((), {}),
                "system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                    },
                ),
                "user_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                    },
                ),
                "max_tokens": ("INT", {"default": 4096, "min": 100, "max": 1e5}),
                "temperature": (
                    "FLOAT",
                    {"min": 0.0, "max": 2.0, "step": 0.01},
                ),
                "top_p": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_llm_model_response"
    OUTPUT_NODE = False
    CATEGORY = "!Axun Nodes/AIAssistant"

    def get_llm_model_response(
        self, model, system_prompt, user_prompt, max_tokens, temperature, top_p
    ):
        if model == "No LLM Enhancement":
            return (user_prompt,)
        
        handler = SiliconCloudHandler()
        response = handler.get_llm_response(
            model,
            system_prompt,
            user_prompt,
            max_tokens,
            temperature,
            top_p,
        )
        ret = json.loads(response)
        text = ret["choices"][0]["message"]["content"]
        return (text,)

class SiliconCloudVLMAPI:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ((), {}),
                "system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                    },
                ),
                "user_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                    },
                ),
                "images": ("IMAGE",),
                "max_tokens": ("INT", {"default": 4096, "min": 100, "max": 1e5}),
                "temperature": (
                    "FLOAT",
                    {"min": 0.0, "max": 2.0, "step": 0.01},
                ),
                "top_p": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "detail": (["auto", "low", "high"], {}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_vlm_model_response"
    OUTPUT_NODE = False
    CATEGORY = "!Axun Nodes/AIAssistant"

    def get_vlm_model_response(
        self, model, system_prompt, user_prompt, images, max_tokens, temperature, top_p, detail
    ):
        if model == "No VLM Enhancement":
            return (user_prompt,)

        encoded_images_json = encode_comfy_image(
            images, image_format="WEBP", lossless=True
        )
        encoded_images_dict = json.loads(encoded_images_json)
        base64_images = list(encoded_images_dict.values())

        handler = SiliconCloudHandler()
        response = handler.get_vlm_response(
            model,
            system_prompt,
            user_prompt,
            base64_images,
            max_tokens,
            temperature,
            top_p,
            detail,
        )
        ret = json.loads(response)
        text = ret["choices"][0]["message"]["content"]
        return (text,)

async def get_llm_models(api_key: str = None) -> List[str]:
    """获取LLM模型列表"""
    print("[AIAssistant] 开始获取LLM模型列表...")
    handler = SiliconCloudHandler()
    if api_key:
        handler.api_key = api_key
    return await handler.fetch_models(model_type="llm")

async def get_vlm_models(api_key: str = None) -> List[str]:
    """获取VLM模型列表"""
    print("[AIAssistant] 开始获取VLM模型列表...")
    handler = SiliconCloudHandler()
    if api_key:
        handler.api_key = api_key
    return await handler.fetch_models(model_type="vlm")

@PromptServer.instance.routes.post("/axun/AIAssistant/llm/models")
async def get_silicon_cloud_llm_models(request):
    """获取LLM模型列表"""
    try:
        data = await request.json()
        api_key = data.get("api_key", "")
        models = await get_llm_models(api_key)
        return web.json_response(models)
    except Exception as e:
        print(f"[AIAssistant] 获取LLM模型列表失败: {e}")
        return web.json_response(["获取模型列表失败"])

@PromptServer.instance.routes.post("/axun/AIAssistant/vlm/models")
async def get_silicon_cloud_vlm_models(request):
    """获取VLM模型列表"""
    try:
        data = await request.json()
        api_key = data.get("api_key", "")
        models = await get_vlm_models(api_key)
        return web.json_response(models)
    except Exception as e:
        print(f"[AIAssistant] 获取VLM模型列表失败: {e}")
        return web.json_response(["获取模型列表失败"])

@PromptServer.instance.routes.post("/axun/AIAssistant/deepseek/models")
async def get_deepseek_llm_models(request):
    """获取DeepSeek LLM模型列表"""
    try:
        data = await request.json()
        api_key = data.get("api_key", "")
        handler = DeepSeekHandler()
        if api_key:
            handler.api_key = api_key
        models = await handler.fetch_models()
        return web.json_response(models)
    except Exception as e:
        print(f"[AIAssistant] 获取DeepSeek LLM模型列表失败: {e}")
        return web.json_response(["获取模型列表失败"])

class DeepSeekLLMAPI:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ((), {}),
                "system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                    },
                ),
                "user_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                    },
                ),
                "max_tokens": ("INT", {"default": 4096, "min": 100, "max": 1e5}),
                "temperature": (
                    "FLOAT",
                    {"min": 0.0, "max": 2.0, "step": 0.01},
                ),
                "top_p": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_llm_model_response"
    OUTPUT_NODE = False
    CATEGORY = "!Axun Nodes/AIAssistant"

    def get_llm_model_response(
        self, model, system_prompt, user_prompt, max_tokens, temperature, top_p
    ):
        if model == "No DeepSeek Enhancement":
            return (user_prompt,)
        
        handler = DeepSeekHandler()
        response = handler.get_llm_response(
            model,
            system_prompt,
            user_prompt,
            max_tokens,
            temperature,
            top_p,
        )
        ret = json.loads(response)
        text = ret["choices"][0]["message"]["content"]
        return (text,)

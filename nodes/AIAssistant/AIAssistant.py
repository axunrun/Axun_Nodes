import json
import asyncio
import aiohttp
from aiohttp import web
from server import PromptServer
from typing import List, Dict
import os

from .utils.api_handler import GenericOpenAIHandler
from .utils.image_utils import encode_comfy_image

class GenericOpenAILLMAPI:
    """通用 OpenAI 格式 LLM API 节点，支持自定义 API 地址"""
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")

    @classmethod
    def INPUT_TYPES(s):
        configs = s.load_api_configs()
        config_names = ["手动输入"] + [config["name"] for config in configs]
        
        return {
            "required": {
                "config_selection": (config_names, {"default": "手动输入"}),
                "base_url": (
                    "STRING",
                    {
                        "default": "https://api.openai.com/v1",
                        "multiline": False,
                    }
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    }
                ),
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
                    {"min": 0.0, "max": 2.0, "step": 0.01, "default": 0.7},
                ),
                "top_p": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01, "default": 0.9},
                ),
            },
            "optional": {
                "save_config": (["不保存", "保存为新配置"], {"default": "不保存"}),
                "config_name": (
                    "STRING",
                    {
                        "default": "新配置",
                        "multiline": False,
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_llm_model_response"
    OUTPUT_NODE = False
    CATEGORY = "!Axun Nodes/AIAssistant"

    @classmethod
    def load_api_configs(cls):
        """加载API配置"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      "config", "AIAssistant_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("api_configs", [])
            return []
        except Exception as e:
            print(f"加载配置失败: {e}")
            return []

    def save_config(self, base_url, api_key, config_name):
        """保存API配置到配置文件"""
        try:
            # 读取现有配置
            all_configs = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
            
            # 确保api_configs字段存在
            if "api_configs" not in all_configs:
                all_configs["api_configs"] = []
            
            # 添加或更新配置
            new_config = {
                "name": config_name,
                "base_url": base_url,
                "api_key": api_key
            }
            
            # 检查是否已存在相同名称的配置
            exists = False
            for i, config in enumerate(all_configs["api_configs"]):
                if config["name"] == config_name:
                    all_configs["api_configs"][i] = new_config
                    exists = True
                    break
            
            if not exists:
                all_configs["api_configs"].append(new_config)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(all_configs, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get_llm_model_response(
        self, config_selection, base_url, api_key, model, system_prompt, user_prompt, 
        max_tokens, temperature, top_p, save_config=None, config_name=None
    ):
        # 如果选择了预设配置，读取配置
        if config_selection != "手动输入":
            configs = self.load_api_configs()
            for config in configs:
                if config["name"] == config_selection:
                    base_url = config["base_url"]
                    api_key = config["api_key"]
                    break
        
        # 如果选择保存配置
        if save_config == "保存为新配置" and config_name:
            self.save_config(base_url, api_key, config_name)
            
        if model == "获取模型列表失败" or model.startswith("获取模型列表失败:"):
            raise Exception(f"模型加载失败: {model}")
        
        handler = GenericOpenAIHandler(base_url=base_url, api_key=api_key)
        
        try:
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
        except Exception as e:
            raise Exception(f"调用 API 失败: {str(e)}")

@PromptServer.instance.routes.post("/axun/AIAssistant/generic_openai/models")
async def get_generic_openai_models(request):
    """获取通用 OpenAI 格式 API 的模型列表"""
    try:
        data = await request.json()
        base_url = data.get("base_url", "https://api.openai.com/v1")
        api_key = data.get("api_key", "")
        
        handler = GenericOpenAIHandler(base_url=base_url, api_key=api_key)
        models = await handler.fetch_models()
        
        return web.json_response(models)
    except Exception as e:
        print(f"[AIAssistant] 获取通用 OpenAI 模型列表失败: {e}")
        return web.json_response([f"获取模型列表失败: {str(e)}"])

@PromptServer.instance.routes.post("/axun/AIAssistant/load_config")
async def load_api_config(request):
    """加载指定名称的API配置"""
    try:
        data = await request.json()
        config_name = data.get("config_name", "")
        
        if not config_name:
            return web.json_response({"error": "未提供配置名称"}, status=400)
        
        # 读取配置文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")
        
        if not os.path.exists(config_path):
            return web.json_response({"error": "配置文件不存在"}, status=404)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)
        
        api_configs = all_configs.get("api_configs", [])
        
        # 查找指定名称的配置
        for config in api_configs:
            if config.get("name") == config_name:
                return web.json_response({
                    "base_url": config.get("base_url", ""),
                    "api_key": config.get("api_key", "")
                })
        
        return web.json_response({"error": f"未找到名称为 '{config_name}' 的配置"}, status=404)
    except Exception as e:
        print(f"[AIAssistant] 加载API配置失败: {e}")
        return web.json_response({"error": f"加载配置失败: {str(e)}"}, status=500)

class GenericOpenAIVLMAPI:
    """通用 OpenAI 格式 VLM API 节点，支持自定义 API 地址和图像分析"""
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")

    @classmethod
    def INPUT_TYPES(s):
        configs = s.load_api_configs()
        config_names = ["手动输入"] + [config["name"] for config in configs]
        
        return {
            "required": {
                "config_selection": (config_names, {"default": "手动输入"}),
                "base_url": (
                    "STRING",
                    {
                        "default": "https://api.openai.com/v1",
                        "multiline": False,
                    }
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    }
                ),
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
                    {"min": 0.0, "max": 2.0, "step": 0.01, "default": 0.7},
                ),
                "top_p": (
                    "FLOAT",
                    {"min": 0.0, "max": 1.0, "step": 0.01, "default": 0.9},
                ),
                "detail": (["auto", "low", "high"], {"default": "auto"}),
            },
            "optional": {
                "save_config": (["不保存", "保存为新配置"], {"default": "不保存"}),
                "config_name": (
                    "STRING",
                    {
                        "default": "新配置",
                        "multiline": False,
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_vlm_model_response"
    OUTPUT_NODE = False
    CATEGORY = "!Axun Nodes/AIAssistant"

    @classmethod
    def load_api_configs(cls):
        """加载API配置"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      "config", "AIAssistant_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("api_configs", [])
            return []
        except Exception as e:
            print(f"加载配置失败: {e}")
            return []

    def save_config(self, base_url, api_key, config_name):
        """保存API配置到配置文件"""
        try:
            # 读取现有配置
            all_configs = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
            
            # 确保api_configs字段存在
            if "api_configs" not in all_configs:
                all_configs["api_configs"] = []
            
            # 添加或更新配置
            new_config = {
                "name": config_name,
                "base_url": base_url,
                "api_key": api_key
            }
            
            # 检查是否已存在相同名称的配置
            exists = False
            for i, config in enumerate(all_configs["api_configs"]):
                if config["name"] == config_name:
                    all_configs["api_configs"][i] = new_config
                    exists = True
                    break
            
            if not exists:
                all_configs["api_configs"].append(new_config)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(all_configs, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get_vlm_model_response(
        self, config_selection, base_url, api_key, model, system_prompt, user_prompt, 
        images, max_tokens, temperature, top_p, detail, save_config=None, config_name=None
    ):
        # 如果选择了预设配置，读取配置
        if config_selection != "手动输入":
            configs = self.load_api_configs()
            for config in configs:
                if config["name"] == config_selection:
                    base_url = config["base_url"]
                    api_key = config["api_key"]
                    break
        
        # 如果选择保存配置
        if save_config == "保存为新配置" and config_name:
            self.save_config(base_url, api_key, config_name)
            
        if model == "获取模型列表失败" or model.startswith("获取模型列表失败:"):
            raise Exception(f"模型加载失败: {model}")
        
        # 编码图像为 base64 格式
        encoded_images_json = encode_comfy_image(
            images, image_format="WEBP", lossless=True
        )
        encoded_images_dict = json.loads(encoded_images_json)
        base64_images = list(encoded_images_dict.values())

        handler = GenericOpenAIHandler(base_url=base_url, api_key=api_key)
        
        try:
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
        except Exception as e:
            raise Exception(f"调用 API 失败: {str(e)}")

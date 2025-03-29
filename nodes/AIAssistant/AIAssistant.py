import json
import asyncio
import aiohttp
from aiohttp import web
from server import PromptServer
from typing import List, Dict
import os
import sys

from .utils.api_handler import GenericOpenAIHandler
from .utils.image_utils import encode_comfy_image

def get_config_path(filename):
    """获取配置文件的路径，固定使用Axun_Nodes/config目录"""
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定位到 Axun_Nodes 目录
    # 当前目录结构: .../custom_nodes/Axun_Nodes/nodes/AIAssistant
    axun_nodes_dir = os.path.dirname(os.path.dirname(current_dir))
    
    # 构造配置文件路径
    config_path = os.path.join(axun_nodes_dir, "config", filename)
    
    # 确保配置目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # 打印配置文件路径进行调试
    abs_path = os.path.abspath(config_path)
    print(f"[AIAssistant] 使用固定配置路径: {abs_path}")
    
    return config_path

class GenericOpenAILLMAPI:
    """通用 OpenAI 格式 LLM API 节点，支持自定义 API 地址"""
    
    def __init__(self):
        self.config_path = get_config_path("AIAssistant_config.json")
        print(f"[AIAssistant] LLM节点使用配置文件路径: {self.config_path}")
        
        # 确保配置文件存在，如果不存在则创建一个带有空api_configs的基础配置
        if not os.path.exists(self.config_path):
            print(f"[AIAssistant] 配置文件不存在，创建默认配置: {self.config_path}")
            default_config = {"api_configs": []}
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)

    @classmethod
    def INPUT_TYPES(s):
        """
        重要：此方法在每次显示节点时都会调用
        确保每次调用都能获取最新的配置列表
        """
        configs = s.load_api_configs()
        config_names = ["手动输入"] + [config["name"] for config in configs]
        
        print(f"[AIAssistant] GenericOpenAILLMAPI.INPUT_TYPES 加载配置列表: {config_names}")
        
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
            config_path = get_config_path("AIAssistant_config.json")
            print(f"[AIAssistant] load_api_configs 使用配置文件路径: {config_path}")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("api_configs", [])
            return []
        except Exception as e:
            print(f"加载配置失败: {e}")
            return []

    def save_config(self, config_name, config_data):
        """保存完整的API配置到配置文件"""
        try:
            # 读取现有配置
            all_configs = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
            
            # 确保api_configs字段存在
            if "api_configs" not in all_configs:
                all_configs["api_configs"] = []
            
            # 检查是否已存在相同名称的配置
            exists = False
            for i, config in enumerate(all_configs["api_configs"]):
                if config["name"] == config_name:
                    all_configs["api_configs"][i] = config_data
                    exists = True
                    print(f"[AIAssistant] 更新配置 '{config_name}'")
                    break
            
            if not exists:
                all_configs["api_configs"].append(config_data)
                print(f"[AIAssistant] 添加新配置 '{config_name}'")
            
            # 记录保存的配置内容
            print(f"[AIAssistant] 保存配置内容: model={config_data.get('model')}, system_prompt长度={len(config_data.get('system_prompt', ''))}, user_prompt长度={len(config_data.get('user_prompt', ''))}")
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(all_configs, f, indent=4, ensure_ascii=False)
                
            print(f"[AIAssistant] 配置成功保存到 {self.config_path}")
            return True
        except Exception as e:
            print(f"[AIAssistant] 保存配置失败: {e}")
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
                    base_url = config.get("base_url", base_url)
                    api_key = config.get("api_key", api_key)
                    
                    # 加载其他保存的参数(如果存在)
                    old_system_prompt = system_prompt
                    old_user_prompt = user_prompt
                    system_prompt = config.get("system_prompt", system_prompt)
                    user_prompt = config.get("user_prompt", user_prompt)
                    max_tokens = config.get("max_tokens", max_tokens)
                    temperature = config.get("temperature", temperature)
                    top_p = config.get("top_p", top_p)
                    model = config.get("model", model)
                    
                    # 记录日志以验证是否成功加载
                    if system_prompt != old_system_prompt:
                        print(f"[AIAssistant] 已加载system_prompt, 长度: {len(system_prompt)}")
                    if user_prompt != old_user_prompt:
                        print(f"[AIAssistant] 已加载user_prompt, 长度: {len(user_prompt)}")
                    break
        
        # 如果选择保存配置
        if save_config == "保存为新配置" and config_name:
            print(f"[AIAssistant] 准备保存配置: {config_name}, system_prompt长度: {len(system_prompt)}, user_prompt长度: {len(user_prompt)}")
            config_data = {
                "name": config_name,
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            self.save_config(config_name, config_data)
        
        if model == "获取模型列表失败" or model.startswith("获取模型列表失败:"):
            print(f"[AIAssistant] 模型加载失败: {model}")
            raise Exception(f"模型加载失败: {model}")
        
        print(f"[AIAssistant] 开始调用API, 模型: {model}, base_url: {base_url}")
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
            print(f"[AIAssistant] API调用成功, 返回内容长度: {len(text)}")
            return (text,)
        except Exception as e:
            print(f"[AIAssistant] API调用失败: {str(e)}")
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
        config_path = get_config_path("AIAssistant_config.json")
        print(f"[AIAssistant] 路由处理函数使用配置文件路径: {config_path}")
        
        if not os.path.exists(config_path):
            print(f"[AIAssistant] 配置文件不存在: {config_path}")
            return web.json_response({"error": "配置文件不存在"}, status=404)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)
        
        api_configs = all_configs.get("api_configs", [])
        print(f"[AIAssistant] 已加载配置列表: {[config.get('name') for config in api_configs]}")
        
        # 查找指定名称的配置
        for config in api_configs:
            if config.get("name") == config_name:
                # 输出配置详情日志
                prompt_length = len(config.get("system_prompt", "")) if "system_prompt" in config else 0
                user_prompt_length = len(config.get("user_prompt", "")) if "user_prompt" in config else 0
                
                print(f"[AIAssistant] 找到配置 '{config_name}', 包含字段: {list(config.keys())}")
                print(f"[AIAssistant] system_prompt长度: {prompt_length}, user_prompt长度: {user_prompt_length}")
                
                # 如果有必要，确保所有字段都存在，避免前端undefined错误
                required_fields = ["base_url", "api_key", "model", "system_prompt", "user_prompt", 
                                  "max_tokens", "temperature", "top_p"]
                
                for field in required_fields:
                    if field not in config:
                        config[field] = "" if field in ["base_url", "api_key", "model", "system_prompt", "user_prompt"] else 0
                
                # 返回完整配置(包括所有扩展字段)
                return web.json_response(config)
        
        print(f"[AIAssistant] 未找到配置 '{config_name}'")
        return web.json_response({"error": f"未找到名称为 '{config_name}' 的配置"}, status=404)
    except Exception as e:
        print(f"[AIAssistant] 加载API配置失败: {e}")
        return web.json_response({"error": f"加载配置失败: {str(e)}"}, status=500)

class GenericOpenAIVLMAPI:
    """通用 OpenAI 格式 VLM API 节点，支持自定义 API 地址和图像分析"""
    
    def __init__(self):
        self.config_path = get_config_path("AIAssistant_config.json")
        print(f"[AIAssistant] VLM节点使用配置文件路径: {self.config_path}")
        
        # 确保配置文件存在，如果不存在则创建一个带有空api_configs的基础配置
        if not os.path.exists(self.config_path):
            print(f"[AIAssistant] 配置文件不存在，创建默认配置: {self.config_path}")
            default_config = {"api_configs": []}
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)

    @classmethod
    def INPUT_TYPES(s):
        """
        重要：此方法在每次显示节点时都会调用
        确保每次调用都能获取最新的配置列表
        """
        configs = s.load_api_configs()
        config_names = ["手动输入"] + [config["name"] for config in configs]
        
        print(f"[AIAssistant] GenericOpenAIVLMAPI.INPUT_TYPES 加载配置列表: {config_names}")
        
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
            config_path = get_config_path("AIAssistant_config.json")
            print(f"[AIAssistant] load_api_configs 使用配置文件路径: {config_path}")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("api_configs", [])
            return []
        except Exception as e:
            print(f"加载配置失败: {e}")
            return []

    def save_config(self, config_name, config_data):
        """保存完整的API配置到配置文件"""
        try:
            # 读取现有配置
            all_configs = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
            
            # 确保api_configs字段存在
            if "api_configs" not in all_configs:
                all_configs["api_configs"] = []
            
            # 检查是否已存在相同名称的配置
            exists = False
            for i, config in enumerate(all_configs["api_configs"]):
                if config["name"] == config_name:
                    all_configs["api_configs"][i] = config_data
                    exists = True
                    print(f"[AIAssistant] 更新配置 '{config_name}'")
                    break
            
            if not exists:
                all_configs["api_configs"].append(config_data)
                print(f"[AIAssistant] 添加新配置 '{config_name}'")
            
            # 记录保存的配置内容
            print(f"[AIAssistant] 保存配置内容: model={config_data.get('model')}, system_prompt长度={len(config_data.get('system_prompt', ''))}, user_prompt长度={len(config_data.get('user_prompt', ''))}")
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(all_configs, f, indent=4, ensure_ascii=False)
                
            print(f"[AIAssistant] 配置成功保存到 {self.config_path}")
            return True
        except Exception as e:
            print(f"[AIAssistant] 保存配置失败: {e}")
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
                    base_url = config.get("base_url", base_url)
                    api_key = config.get("api_key", api_key)
                    
                    # 加载其他保存的参数(如果存在)
                    old_system_prompt = system_prompt
                    old_user_prompt = user_prompt
                    system_prompt = config.get("system_prompt", system_prompt)
                    user_prompt = config.get("user_prompt", user_prompt)
                    max_tokens = config.get("max_tokens", max_tokens)
                    temperature = config.get("temperature", temperature)
                    top_p = config.get("top_p", top_p)
                    model = config.get("model", model)
                    detail = config.get("detail", detail)
                    
                    # 记录日志以验证是否成功加载
                    if system_prompt != old_system_prompt:
                        print(f"[AIAssistant] VLM: 已加载system_prompt, 长度: {len(system_prompt)}")
                    if user_prompt != old_user_prompt:
                        print(f"[AIAssistant] VLM: 已加载user_prompt, 长度: {len(user_prompt)}")
                    break
        
        # 如果选择保存配置
        if save_config == "保存为新配置" and config_name:
            print(f"[AIAssistant] VLM: 准备保存配置: {config_name}, system_prompt长度: {len(system_prompt)}, user_prompt长度: {len(user_prompt)}")
            config_data = {
                "name": config_name,
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "detail": detail
            }
            self.save_config(config_name, config_data)
        
        if model == "获取模型列表失败" or model.startswith("获取模型列表失败:"):
            print(f"[AIAssistant] 模型加载失败: {model}")
            raise Exception(f"模型加载失败: {model}")
        
        # 编码图像为 base64 格式
        encoded_images_json = encode_comfy_image(
            images, image_format="WEBP", lossless=True
        )
        encoded_images_dict = json.loads(encoded_images_json)
        base64_images = list(encoded_images_dict.values())
        print(f"[AIAssistant] 已编码 {len(base64_images)} 张图像")

        print(f"[AIAssistant] 开始调用API, 模型: {model}, base_url: {base_url}")
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
            print(f"[AIAssistant] API调用成功, 返回内容长度: {len(text)}")
            return (text,)
        except Exception as e:
            print(f"[AIAssistant] API调用失败: {str(e)}")
            raise Exception(f"调用 API 失败: {str(e)}")

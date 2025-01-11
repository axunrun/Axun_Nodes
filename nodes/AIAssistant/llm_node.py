"""
LLM节点实现
用途：处理LLM相关的API调用和响应
"""

import json
import logging
from typing import Dict, Tuple, Optional
import os
import asyncio
import torch
from torch import Tensor

# 获取当前模块所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))

# 导入工具函数
from .utils import (
    load_llm_config,
    fetch_llm_models,
    get_llm_response,
    get_vlm_response,
    encode_image_for_vlm,
    load_llm_prompts,
    save_llm_prompts,
    delete_llm_prompts
)

logger = logging.getLogger('axun.llm')

class LLMNode:
    """LLM节点类
    
    功能：
    1. 管理LLM配置
    2. 处理模型请求
    3. 管理会话状态
    """
    
    CONFIG_FILE = os.path.join(PLUGIN_ROOT, "config", "llm_config.json")
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMNode, cls).__new__(cls)
            cls._instance.init_config()
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.last_provider = None
            self.node_id = None
            self.prompts = None
            self.initialized = True

    def init_config(self) -> None:
        """初始化配置"""
        try:
            logger.info("[LLM Debug - 启动] 开始初始化LLM配置...")
            
            # 加载配置
            self._config = load_llm_config()
            if not self._config or "providers" not in self._config:
                raise ValueError("配置文件无效: 缺少providers字段")
            
            # 验证配置结构
            self._validate_config()
            
            # 启动时更新一次模型列表
            logger.info("[LLM Debug - 启动] 开始获取所有服务商的模型列表...")
            self._update_models_on_startup()
            
            logger.info("[LLM Debug - 启动] LLM配置初始化完成")
            
        except Exception as e:
            logger.error(f"[LLM Debug - 启动] 初始化配置失败: {e}")
            self._config = self._get_default_config()

    def _validate_config(self) -> None:
        """验证配置文件结构"""
        required_fields = {
            "providers": dict,
            "default_parameters": dict
        }
        
        for field, field_type in required_fields.items():
            if field not in self._config:
                raise ValueError(f"配置文件缺少必要字段: {field}")
            if not isinstance(self._config[field], field_type):
                raise TypeError(f"配置字段类型错误: {field} 应为 {field_type.__name__}")

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "providers": {
                "Silicon Cloud LLM": {
                    "api_key": "",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "models": [],
                    "default_model": "Qwen/Qwen2.5-7B-Instruct",
                    "capabilities": ["text"]
                },
                "Silicon Cloud VLM": {
                    "api_key": "",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "models": [],
                    "default_model": "Qwen/Qwen2-VL-72B-Instruct",
                    "capabilities": ["text", "image"]
                },
                "Deepseek": {
                    "api_key": "",
                    "base_url": "https://api.deepseek.com/v1",
                    "models": [],
                    "default_model": "deepseek-chat",
                    "capabilities": ["text"]
                }
            },
            "default_parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 512
            }
        }

    def _update_models_on_startup(self) -> None:
        """启动时更新模型列表"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            if loop.is_running():
                future = asyncio.ensure_future(self.update_all_models())
                loop.run_until_complete(future)
            else:
                loop.run_until_complete(self.update_all_models())
            
            # 打印每个提供商的模型列表
            for provider, data in self._config["providers"].items():
                models = data.get("models", [])
                if models:
                    logger.info(f"[LLM Debug - 启动] {provider} 可用模型: {', '.join(models)}")
                else:
                    logger.warning(f"[LLM Debug - 启动] {provider} 没有可用模型")
                    
        except Exception as e:
            logger.error(f"[LLM Debug - 启动] 更新模型列表失败: {e}")

    async def update_all_models(self) -> None:
        """更新所有服务商的模型列表"""
        logger.info("[LLM Debug] 开始更新所有服务商的模型列表")
        try:
            for provider in self._config["providers"].keys():
                models = await fetch_llm_models(provider)
                self._config["providers"][provider]["models"] = models
            logger.info("[LLM Debug] 所有服务商的模型列表更新完成")
        except Exception as e:
            logger.error(f"[LLM Debug] 更新所有模型列表失败: {e}")

    @classmethod
    def INPUT_TYPES(cls):
        """获取输入类型"""
        if cls._config is None:
            if cls._instance is None:
                cls._instance = cls()
            cls._config = cls._instance._config

        # 获取提供商列表
        providers = list(cls._config.get("providers", {}).keys())
        if not providers:
            providers = ["Silicon Cloud LLM", "Silicon Cloud VLM", "Deepseek"]
        
        # 获取默认提供商的模型列表
        default_provider = providers[0]
        provider_config = cls._config["providers"].get(default_provider, {})
        models = provider_config.get("models", [provider_config.get("default_model", "Qwen/Qwen2.5-7B-Instruct")])
        
        # 获取默认参数
        default_params = cls._config.get("default_parameters", {})
        
        logger.info(f"[LLM Debug] INPUT_TYPES - providers: {providers}")
        logger.info(f"[LLM Debug] INPUT_TYPES - models: {models}")
        
        return {
            "required": {
                "provider": (providers, {
                    "default": default_provider,
                    "tooltip": "选择LLM服务提供商"
                }),
                "model": (models, {
                    "default": models[0] if models else provider_config.get("default_model", "Qwen/Qwen2.5-7B-Instruct"),
                    "tooltip": "选择模型"
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "你是一个 stable diffusion prompt 专家，为我生成适用于 Stable Diffusion 模型的prompt。 我给你相关的单词，你帮我扩写为适合 Stable Diffusion 文生图的 prompt。要求： 1. 英文输出 2. 除了 prompt 外，不要输出任何其它的信息",
                    "tooltip": "系统提示词，用于设置AI助手的角色和行为"
                }),
                "user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "梵高风格的小猫",
                    "tooltip": "用户提示词，即你想要AI回答的问题或要求"
                }),
                "temperature": ("FLOAT", {
                    "default": default_params.get("temperature", 0.7),
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "tooltip": "温度参数，控制输出的随机性。值越高，回答越有创意；值越低，回答越确定"
                }),
                "top_p": ("FLOAT", {
                    "default": default_params.get("top_p", 0.9),
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "采样范围，控制输出的多样性"
                }),
                "max_tokens": ("INT", {
                    "default": default_params.get("max_tokens", 512),
                    "min": 100,
                    "max": 2048,
                    "step": 1,
                    "tooltip": "生成文本的最大长度"
                }),
            },
            "optional": {
                "image": ("IMAGE",),
                "detail": (["auto", "low", "high"], {"default": "auto"})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"
    OUTPUT_NODE = False
    CATEGORY = "!Axun Nodes/LLM"

    def get_model_list(self, provider: str) -> list:
        """获取当前提供商的模型列表"""
        return self._config["providers"].get(provider, {}).get("models", [])

    def _handle_error(self, error: Exception) -> str:
        """统一错误处理"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        error_map = {
            "ValueError": "参数错误",
            "TypeError": "类型错误",
            "ConnectionError": "连接错误",
            "TimeoutError": "请求超时",
            "KeyError": "配置错误",
            "RuntimeError": "运行时错误",
            "Exception": "未知错误"
        }
        
        prefix = error_map.get(error_type, "未知错误")
        return f"{prefix}: {error_msg}"

    def generate(self, provider: str, model: str,
                system_prompt: str, user_prompt: str, max_tokens: int,
                temperature: float, top_p: float, image: Optional[Tensor] = None,
                detail: str = "auto", id: str = None) -> Tuple[str]:
        """生成回复"""
        try:
            # 第一次运行时加载prompts
            if self.node_id != id:
                self.node_id = id
                self.prompts = load_llm_prompts(id)
                logger.info(f"[LLM Debug] 加载节点 {id} 的prompt预设")
            
            # 切换提供商时更新模型列表
            if provider != self.last_provider:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                try:
                    if loop.is_running():
                        future = asyncio.ensure_future(fetch_llm_models(provider))
                        loop.run_until_complete(future)
                    else:
                        loop.run_until_complete(fetch_llm_models(provider))
                    
                    available_models = self.get_model_list(provider)
                    if not model or model not in available_models:
                        model = available_models[0] if available_models else self._config["providers"][provider]["default_model"]
                        logger.info(f"[LLM Debug] 使用默认模型: {model}")
                    
                    self.last_provider = provider
                except Exception as e:
                    logger.error(f"[LLM Debug] 更新模型列表失败: {e}")
            
            # 检查提供商能力
            provider_config = self._config["providers"].get(provider, {})
            capabilities = provider_config.get("capabilities", [])
            
            if image is not None and "image" not in capabilities:
                raise ValueError(f"提供商 {provider} 不支持图像输入")
            
            # 创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 生成回复
            if image is not None:
                encoded_image = encode_image_for_vlm(image)
                response = loop.run_until_complete(
                    get_vlm_response(
                        provider=provider,
                        model=model,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        base64_images=[encoded_image],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        detail=detail
                    )
                )
            else:
                response = loop.run_until_complete(
                    get_llm_response(
                        provider=provider,
                        model=model,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p
                    )
                )
            
            # 解析响应
            ret = json.loads(response)
            text = ret["choices"][0]["message"]["content"]
            return (text,)
            
        except Exception as e:
            error_msg = self._handle_error(e)
            logger.error(f"[LLM Debug] {error_msg}")
            return (error_msg,) 
"""
API处理器模块
用途：处理各种API请求的基础类和实现
"""

import json
import os
import aiohttp
import asyncio
import random
from typing import Dict, List, Optional
from aiohttp import web

# 固定参数配置
FIXED_PARAMS = {
    "Silicon Cloud LLM": {
        "stream": False,
        "top_k": 50,
        "n": 1
    },
    "Silicon Cloud VLM": {
        "stream": False,
        "top_k": 50,
        "n": 1
    },
    "Deepseek": {
        "stream": False,
        "presence_penalty": 0.5,
        "frequency_penalty": 0.5
    }
}

class BaseAPIHandler:
    """基础API处理器"""
    def __init__(self):
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                "config", "llm_config.json")
        try:
            if not os.path.exists(config_path):
                print(f"[API Handler] 配置文件不存在: {config_path}")
                return self.get_default_config()
                
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[API Handler] 成功加载配置")
                return config
        except Exception as e:
            print(f"[API Handler] 加载配置失败: {str(e)}")
            return self.get_default_config()
            
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "providers": {
                "Silicon Cloud LLM": {
                    "api_key": "",
                    "models": ["Qwen/Qwen2.5-7B-Instruct"],
                    "default_model": "Qwen/Qwen2.5-7B-Instruct"
                },
                "Silicon Cloud VLM": {
                    "api_key": "",
                    "models": ["Qwen/Qwen2-VL-72B-Instruct"],
                    "default_model": "Qwen/Qwen2-VL-72B-Instruct"
                },
                "Deepseek": {
                    "api_key": "",
                    "models": ["deepseek-chat", "deepseek-coder"],
                    "default_model": "deepseek-chat"
                }
            },
            "api_config": {
                "Silicon Cloud LLM": {
                    "base_url": "https://api.siliconflow.cn/v1",
                    "models_endpoint": "/models",
                    "chat_endpoint": "/chat/completions",
                    "retry_times": 3,
                    "retry_delay": 1,
                    "timeout": 30
                },
                "Silicon Cloud VLM": {
                    "base_url": "https://api.siliconflow.cn/v1",
                    "models_endpoint": "/models",
                    "chat_endpoint": "/chat/completions",
                    "retry_times": 3,
                    "retry_delay": 1,
                    "timeout": 30
                },
                "Deepseek": {
                    "base_url": "https://api.deepseek.com",
                    "models_endpoint": "/v1/models",
                    "chat_endpoint": "/chat/completions",
                    "retry_times": 3,
                    "retry_delay": 1,
                    "timeout": 30
                }
            }
        }

    async def validate_api_key(self, provider: str) -> bool:
        """验证API密钥是否有效"""
        try:
            provider_config = self.config["providers"].get(provider)
            api_config = self.config["api_config"].get(provider)
            
            if not provider_config or not api_config:
                raise ValueError(f"未找到提供商配置: {provider}")
                
            api_key = provider_config.get("api_key")
            if not api_key:
                raise ValueError(f"未设置API密钥: {provider}")
            
            # 构建请求头
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {api_key}"
            }
            
            # 发送验证请求
            if "Silicon Cloud" in provider:
                url = f"{api_config['base_url']}{api_config['models_endpoint']}"
                params = {"type": "text", "sub_type": "chat"}
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        return response.status == 200
            elif provider == "Deepseek":
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=api_config["base_url"]
                )
                try:
                    # 使用 chat endpoint 验证 API key
                    response = await client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1
                    )
                    return True
                except Exception:
                    return False
                    
            return False
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False

    async def _make_request(self, method: str, url: str, headers: Dict = None,
                          params: Dict = None, json_data: Dict = None,
                          provider: str = None) -> Dict:
        """发送HTTP请求，带重试机制"""
        if not provider:
            raise ValueError("必须指定provider")
            
        api_config = self.config["api_config"].get(provider)
        if not api_config:
            raise ValueError(f"未找到API配置: {provider}")
            
        retry_times = api_config.get("retry_times", 3)
        retry_delay = api_config.get("retry_delay", 1)
        timeout = api_config.get("timeout", 30)
        
        for i in range(retry_times):
            try:
                timeout_obj = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise aiohttp.ClientError(f"请求失败: {response.status} - {error_text}")
                        return await response.json()
            except Exception as e:
                if i == retry_times - 1:
                    raise
                delay = retry_delay * (2 ** i) + random.uniform(0, 1)
                print(f"请求失败，{delay}秒后重试: {str(e)}")
                await asyncio.sleep(delay)

    async def update_models(self, provider: str) -> None:
        """更新模型列表到配置文件"""
        try:
            models = await self.fetch_models(provider)
            if models:
                self.config["providers"][provider]["models"] = models
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                        "config", "llm_config.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                print(f"[API Handler] 更新{provider}模型列表成功")
        except Exception as e:
            print(f"[API Handler] 更新模型列表失败: {str(e)}")

    async def fetch_models(self) -> List[str]:
        """获取模型列表"""
        raise NotImplementedError
    
    async def generate_response(self, model: str, system_prompt: str, 
                              user_prompt: str, params: Dict) -> str:
        """生成回复"""
        raise NotImplementedError

class SiliconCloudHandler(BaseAPIHandler):
    """Silicon Cloud API处理器"""
    async def fetch_models(self, provider: str) -> List[str]:
        """获取 Silicon Cloud 的模型列表"""
        api_config = self.config["api_config"].get(provider)
        provider_config = self.config["providers"].get(provider)
        
        if not api_config or not provider_config:
            raise ValueError(f"未找到配置: {provider}")
            
        url = f"{api_config['base_url']}{api_config['models_endpoint']}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {provider_config['api_key']}"
        }
        params = {
            "type": "text",
            "sub_type": "chat"
        }
        
        try:
            response = await self._make_request(
                method="GET",
                url=url,
                headers=headers,
                params=params,
                provider=provider
            )
            
            models = [model["id"] for model in response.get("data", [])]
            if not models:
                return [provider_config["default_model"]]
            return models
            
        except Exception as e:
            print(f"Error fetching Silicon Cloud models: {e}")
            return [provider_config["default_model"]]
            
    async def generate_response(self, provider: str, model: str,
                              system_prompt: str, user_prompt: str,
                              params: Dict) -> str:
        """生成回复"""
        api_config = self.config["api_config"].get(provider)
        provider_config = self.config["providers"].get(provider)
        
        if not api_config or not provider_config:
            raise ValueError(f"未找到配置: {provider}")
            
        url = f"{api_config['base_url']}{api_config['chat_endpoint']}"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {provider_config['api_key']}"
        }
        
        # 合并用户参数和固定参数
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "max_tokens": params.get("max_tokens", 512),
            **FIXED_PARAMS[provider]
        }
        
        try:
            response = await self._make_request(
                method="POST",
                url=url,
                headers=headers,
                json_data=data,
                provider=provider
            )
            return response
            
        except Exception as e:
            raise RuntimeError(f"生成回复失败: {str(e)}")

class DeepseekHandler(BaseAPIHandler):
    """Deepseek API处理器"""
    async def fetch_models(self, provider: str = "Deepseek") -> List[str]:
        """获取 Deepseek 的模型列表"""
        try:
            provider_config = self.config["providers"].get(provider)
            api_config = self.config["api_config"].get(provider)
            
            if not provider_config or not api_config:
                raise ValueError(f"未找到配置: {provider}")
            
            # 构建请求头
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {provider_config['api_key']}"
            }
            
            # 直接使用 aiohttp 请求模型列表
            url = f"{api_config['base_url']}{api_config['models_endpoint']}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            models = [model["id"] for model in data if "id" in model]
                            if models:
                                return models
                    
            # 如果获取失败，返回默认模型列表
            return provider_config["models"]
            
        except Exception as e:
            print(f"Error fetching Deepseek models: {e}")
            return provider_config["models"]
            
    async def generate_response(self, provider: str, model: str,
                              system_prompt: str, user_prompt: str,
                              params: Dict) -> str:
        """生成回复"""
        try:
            from openai import AsyncOpenAI
            
            provider_config = self.config["providers"].get(provider)
            api_config = self.config["api_config"].get(provider)
            
            if not provider_config or not api_config:
                raise ValueError(f"未找到配置: {provider}")
            
            client = AsyncOpenAI(
                api_key=provider_config["api_key"],
                base_url=api_config["base_url"]
            )
            
            # 合并用户参数和固定参数
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=params.get("temperature", 0.7),
                top_p=params.get("top_p", 0.9),
                max_tokens=params.get("max_tokens", 512),
                **FIXED_PARAMS[provider]
            )
            
            return response
            
        except Exception as e:
            raise RuntimeError(f"生成回复失败: {str(e)}")

class TranslatorHandler(BaseAPIHandler):
    """翻译服务处理器"""
    def __init__(self):
        super().__init__()
        
    async def translate(self, text: str) -> Dict:
        """
        翻译文本
        Args:
            text: 要翻译的文本
        Returns:
            Dict: 包含翻译结果的字典
        """
        try:
            # 这里可以根据需要实现具体的翻译逻辑
            # 目前返回一个简单的成功响应
            return {
                "success": True,
                "translated": text,  # 暂时返回原文
                "source_lang": "auto",
                "target_lang": "en"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# 导出工具函数
def load_config() -> Dict:
    """加载配置"""
    handler = BaseAPIHandler()
    return handler.load_config()

async def fetch_models(provider: str) -> List[str]:
    """获取模型列表"""
    if "Silicon Cloud" in provider:
        handler = SiliconCloudHandler()
    else:
        handler = DeepseekHandler()
    return await handler.fetch_models(provider)

async def get_llm_response(provider: str, model: str, system_prompt: str,
                          user_prompt: str, max_tokens: int,
                          temperature: float, top_p: float) -> str:
    """获取LLM回复"""
    params = {
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }
    
    if "Silicon Cloud" in provider:
        handler = SiliconCloudHandler()
    else:
        handler = DeepseekHandler()
        
    return await handler.generate_response(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        params=params
    )

async def get_vlm_response(provider: str, model: str, system_prompt: str,
                          user_prompt: str, base64_images: List[str],
                          max_tokens: int, temperature: float,
                          top_p: float, detail: str = "auto") -> str:
    """获取VLM回复"""
    if provider != "Silicon Cloud VLM":
        raise ValueError("仅支持Silicon Cloud VLM")
        
    handler = SiliconCloudHandler()
    provider_config = handler.config["providers"].get(provider)
    api_config = handler.config["api_config"].get(provider)
    
    if not provider_config or not api_config:
        raise ValueError(f"未找到配置: {provider}")
        
    url = f"{api_config['base_url']}{api_config['chat_endpoint']}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {provider_config['api_key']}"
    }
    
    # 合并用户参数和固定参数
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt}
                ] + [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                    for img in base64_images
                ]
            }
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "detail": detail,
        **FIXED_PARAMS[provider]
    }
    
    try:
        response = await handler._make_request(
            method="POST",
            url=url,
            headers=headers,
            json_data=data,
            provider=provider
        )
        return response
        
    except Exception as e:
        raise RuntimeError(f"生成回复失败: {str(e)}") 
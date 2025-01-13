import base64
import json
import os
import pickle
import urllib.parse
import urllib.request
import zlib
from typing import List, Tuple, Union

import numpy as np
import aiohttp
import asyncio

BIZYAIR_DEBUG = os.getenv("BIZYAIR_DEBUG", False)


def send_post_request(api_url, payload, headers):
    """
    Sends a POST request to the specified API URL with the given payload and headers.

    Args:
        api_url (str): The URL of the API endpoint.
        payload (dict): The payload to send in the POST request.
        headers (dict): The headers to include in the POST request.

    Raises:
        Exception: If there is an error connecting to the server or the request fails.
    """
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode("utf-8")
        return response_data
    except urllib.error.URLError as e:
        if "Unauthorized" in str(e):
            raise Exception(
                "Key is invalid, please refer to https://cloud.siliconflow.cn to get the API key.\n"
                "If you have the key, please click the 'BizyAir Key' button at the bottom right to set the key."
            )
        else:
            raise Exception(
                f"Failed to connect to the server: {e}, if you have no key, "
            )


def serialize_and_encode(obj: Union[np.ndarray], compress=True) -> Tuple[str, bool]:
    """
    Serializes a Python object, optionally compresses it, and then encodes it in base64.

    Args:
        obj: The Python object to serialize.
        compress (bool): Whether to compress the serialized object using zlib. Default is True.

    Returns:
        str: The base64 encoded string of the serialized (and optionally compressed) object.
    """
    serialized_obj = pickle.dumps(obj)

    if compress:
        serialized_obj = zlib.compress(serialized_obj)

    if BIZYAIR_DEBUG:
        print(
            f"serialize_and_encode: size of bytes is {format_bytes(len(serialized_obj))}"
        )

    encoded_obj = base64.b64encode(serialized_obj).decode("utf-8")

    if BIZYAIR_DEBUG:
        print(
            f"serialize_and_encode: size of base64 text is {format_bytes(len(serialized_obj))}"
        )

    return (encoded_obj, compress)


def decode_and_deserialize(response_text) -> np.ndarray:
    if BIZYAIR_DEBUG:
        print(
            f"decode_and_deserialize: size of text is {format_bytes(len(response_text))}"
        )

    ret = json.loads(response_text)

    if "result" in ret:
        msg = json.loads(ret["result"])
    else:
        msg = ret
    if msg["type"] not in (
        "comfyair",
        "bizyair",
    ):  # DO NOT CHANGE THIS LINE: "comfyair" is the type from the server node
        # TODO: change both server and client "comfyair" to "bizyair"
        raise Exception(f"Unexpected response type: {msg}")

    data = msg["data"]

    tensor_bytes = base64.b64decode(data["payload"])
    if data.get("is_compress", None):
        tensor_bytes = zlib.decompress(tensor_bytes)

    if BIZYAIR_DEBUG:
        print(
            f"decode_and_deserialize: size of bytes is {format_bytes(len(tensor_bytes))}"
        )

    deserialized_object = pickle.loads(tensor_bytes)
    return deserialized_object


def format_bytes(num_bytes: int) -> str:
    """
    Converts a number of bytes to a human-readable string with units (B, KB, or MB).

    :param num_bytes: The number of bytes to convert.
    :return: A string representing the number of bytes in a human-readable format.
    """
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def get_api_key():
    from .auth import API_KEY

    return API_KEY


def get_llm_response(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8192,
    temperature: float = 0.7,
):
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEY = get_api_key()
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 50,
        "stream": False,
        "n": 1,
    }
    response = send_post_request(api_url, headers=headers, payload=payload)
    return response


def get_vlm_response(
    model: str,
    system_prompt: str,
    user_prompt: str,
    base64_images: List[str],
    max_tokens: int = 8192,
    temperature: float = 0.7,
    detail: str = "auto",
):
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEY = get_api_key()
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": system_prompt}],
        },  # 此方法皆适用于两种 VL 模型
        # {
        #     "role": "system",
        #     "content": system_prompt,
        # },  # role 为 "system" 的这种方式只适用于 QwenVL 系列模型,并不适用于 InternVL 系列模型
    ]

    user_content = []
    for base64_image in base64_images:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/webp;base64,{base64_image}",
                    "detail": detail,
                },
            }
        )
    user_content.append({"type": "text", "text": user_prompt})

    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 50,
        "stream": False,
        "n": 1,
    }

    response = send_post_request(api_url, headers=headers, payload=payload)
    return response


class SiliconCloudHandler:
    def __init__(self):
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取插件根目录
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        # 配置文件路径
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 如果配置文件不存在，创建默认配置
            if not os.path.exists(self.config_path):
                default_config = {
                    "silicon_llm": {
                        "api_key": "",
                        "api_base": "https://api.siliconflow.cn/v1",
                        "model_list_endpoint": "/models",
                        "chat_endpoint": "/chat/completions",
                        "default_system_prompt": "你是一个 stable diffusion prompt 专家，为我生成适用于 Stable Diffusion 模型的prompt。",
                        "default_max_tokens": 512,
                        "default_temperature": 0.7,
                        "default_top_p": 0.9
                    },
                    "silicon_vlm": {
                        "api_key": "",
                        "api_base": "https://api.siliconflow.cn/v1",
                        "model_list_endpoint": "/models",
                        "chat_endpoint": "/chat/completions",
                        "default_system_prompt": "你是一个能分析图像的AI助手。请仔细观察图像，并根据用户的问题提供详细、准确的描述。",
                        "default_max_tokens": 512,
                        "default_temperature": 0.7,
                        "default_top_p": 0.9,
                        "default_detail": "auto"
                    }
                }
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
                print(f"[Silicon] 已创建默认配置文件: {self.config_path}")
            
            # 读取配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                llm_config = config.get("silicon_llm", {})
                vlm_config = config.get("silicon_vlm", {})
                
                # 加载 LLM 配置
                self.api_key = llm_config.get("api_key", "")
                self.api_base = llm_config.get("api_base", "https://api.siliconflow.cn/v1")
                self.model_list_endpoint = llm_config.get("model_list_endpoint", "/models")
                self.chat_endpoint = llm_config.get("chat_endpoint", "/chat/completions")
                
                # 加载 VLM 特有配置
                self.vlm_api_key = vlm_config.get("api_key", self.api_key)  # 如果未设置，使用 LLM 的 key
                self.vlm_api_base = vlm_config.get("api_base", self.api_base)
                self.vlm_model_list_endpoint = vlm_config.get("model_list_endpoint", self.model_list_endpoint)
                self.vlm_chat_endpoint = vlm_config.get("chat_endpoint", self.chat_endpoint)
        except Exception as e:
            print(f"[Silicon] 加载配置文件失败: {e}")
            self.api_key = ""
            self.api_base = "https://api.siliconflow.cn/v1"
            self.model_list_endpoint = "/models"
            self.chat_endpoint = "/chat/completions"
            self.vlm_api_key = self.api_key
            self.vlm_api_base = self.api_base
            self.vlm_model_list_endpoint = self.model_list_endpoint
            self.vlm_chat_endpoint = self.chat_endpoint

    async def fetch_models(self, model_type: str = "llm") -> List[str]:
        """获取可用模型列表
        
        Args:
            model_type: 模型类型, "llm" 或 "vlm"
            
        Returns:
            List[str]: 模型ID列表
        """
        # 根据类型选择配置
        if model_type == "vlm":
            url = f"{self.vlm_api_base}{self.vlm_model_list_endpoint}"
            api_key = self.vlm_api_key
        else:
            url = f"{self.api_base}{self.model_list_endpoint}"
            api_key = self.api_key
        
        # 固定使用 text 和 chat 参数
        params = {
            "type": "text",
            "sub_type": "chat"
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["id"] for model in data["data"]]
                        
                        # 根据类型过滤模型
                        if model_type == "vlm":
                            # VLM 模型包含 "vl"
                            models = [m for m in models if "vl" in m.lower()]
                            models.append("No VLM Enhancement")
                        else:
                            # LLM 模型不包含 "vl"
                            models = [m for m in models if "vl" not in m.lower()]
                            models.append("No LLM Enhancement")
                            
                        print(f"[Silicon] 获取{model_type.upper()}模型列表成功: {models}")
                        return models
                    else:
                        print(f"[Silicon] 获取模型列表失败: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"[Silicon] 获取模型列表失败: {e}")
            return []

    def get_llm_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """获取LLM响应"""
        url = f"{self.api_base}{self.chat_endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "top_p": top_p,
            "top_k": 50,
            "n": 1,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5
        }
        
        try:
            import urllib.request
            import urllib.error
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req) as response:
                response_text = response.read().decode('utf-8')
                response_json = json.loads(response_text)
                
                # 检查响应格式
                if "error" in response_json:
                    error_msg = response_json["error"].get("message", "Unknown error")
                    print(f"[Silicon] API错误: {error_msg}")
                    return json.dumps({
                        "choices": [{
                            "message": {
                                "content": f"API错误: {error_msg}"
                            }
                        }]
                    })
                
                # 确保响应包含必要的字段
                if "choices" not in response_json or not response_json["choices"]:
                    print(f"[Silicon] 响应格式错误: {response_text}")
                    return json.dumps({
                        "choices": [{
                            "message": {
                                "content": "响应格式错误，请检查API配置"
                            }
                        }]
                    })
                
                return response_text
                
        except Exception as e:
            error_msg = str(e)
            print(f"[Silicon] 请求失败: {error_msg}")
            return json.dumps({
                "choices": [{
                    "message": {
                        "content": f"请求失败: {error_msg}"
                    }
                }]
            })

    def get_vlm_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        base64_images: List[str],
        max_tokens: int = 8192,
        temperature: float = 0.7,
        top_p: float = 0.9,
        detail: str = "auto"
    ) -> str:
        """获取VLM响应"""
        url = f"{self.vlm_api_base}{self.vlm_chat_endpoint}"
        headers = {
            "Authorization": f"Bearer {self.vlm_api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 构建用户消息内容
        user_content = []
        for base64_image in base64_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/webp;base64,{base64_image}",
                    "detail": detail
                }
            })
        user_content.append({"type": "text", "text": user_prompt})
        messages.append({"role": "user", "content": user_content})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "top_p": top_p,
            "top_k": 50,
            "n": 1,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5
        }
        
        try:
            import urllib.request
            import urllib.error
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            error_msg = {"error": {"message": str(e)}}
            return json.dumps(error_msg)


class DeepSeekHandler:
    def __init__(self):
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取插件根目录
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        # 配置文件路径
        self.config_path = os.path.join(plugin_dir, "config", "AIAssistant_config.json")
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                deepseek_config = config.get("deepseek", {})
                self.api_key = deepseek_config.get("api_key", "")
                self.api_base = deepseek_config.get("api_base", "https://api.deepseek.com")
                self.model_list_endpoint = deepseek_config.get("model_list_endpoint", "/models")
                self.chat_endpoint = deepseek_config.get("chat_endpoint", "/chat/completions")
                self.default_max_tokens = deepseek_config.get("default_max_tokens", 2048)
                self.default_temperature = deepseek_config.get("default_temperature", 0.7)
                self.default_top_p = deepseek_config.get("default_top_p", 0.9)
        except Exception as e:
            print(f"[AIAssistant] 加载DeepSeek配置文件失败: {e}")
            self.api_key = ""
            self.api_base = "https://api.deepseek.com"
            self.model_list_endpoint = "/models"
            self.chat_endpoint = "/chat/completions"
            self.default_max_tokens = 2048
            self.default_temperature = 0.7
            self.default_top_p = 0.9

    async def fetch_models(self) -> List[str]:
        """获取可用模型列表"""
        url = f"{self.api_base}{self.model_list_endpoint}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["id"] for model in data.get("data", [])]
                        models.append("No DeepSeek Enhancement")
                        print(f"[AIAssistant] 获取DeepSeek模型列表成功: {models}")
                        return models
                    else:
                        print(f"[AIAssistant] 获取DeepSeek模型列表失败: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"[AIAssistant] 获取DeepSeek模型列表失败: {e}")
            return []

    def get_llm_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> str:
        """获取LLM响应"""
        url = f"{self.api_base}{self.chat_endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
            "n": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "response_format": {"type": "text"},
            "stop": None,
            "stream_options": None,
            "tool_choice": "none",
            "logprobs": False,
            "top_logprobs": None
        }
        
        try:
            import requests
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            error_msg = str(e)
            print(f"[AIAssistant] DeepSeek请求失败: {error_msg}")
            return json.dumps({
                "choices": [{
                    "message": {
                        "content": f"请求失败: {error_msg}"
                    }
                }]
            })

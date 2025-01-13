"""
API路由处理函数
用途：处理各种API请求的路由处理器
"""

import os
import json
from aiohttp import web
from typing import List, Dict, Any

from .api_handler import (
    TranslatorHandler,
    SiliconCloudHandler,
    DeepseekHandler,
    load_config
)

# 获取当前模块所在目录
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(UTILS_DIR)

async def handle_translate_text(request: web.Request) -> web.Response:
    """翻译文本路由处理器"""
    try:
        data = await request.json()
        text = data.get('text', '')
        
        handler = TranslatorHandler()
        result = await handler.translate(text)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)

async def handle_silicon_cloud_llm_models(request: web.Request) -> web.Response:
    """Silicon Cloud LLM模型获取路由处理器"""
    try:
        handler = SiliconCloudHandler()
        models = await handler.fetch_models()
        llm_models = [model for model in models if "vl" not in model.lower()]
        return web.json_response(llm_models)
    except Exception as e:
        print(f"Error fetching Silicon Cloud LLM models: {e}")
        return web.json_response([])

async def handle_silicon_cloud_vlm_models(request: web.Request) -> web.Response:
    """Silicon Cloud VLM模型获取路由处理器"""
    try:
        handler = SiliconCloudHandler()
        models = await handler.fetch_models()
        vlm_models = [model for model in models if "vl" in model.lower()]
        return web.json_response(vlm_models)
    except Exception as e:
        print(f"Error fetching Silicon Cloud VLM models: {e}")
        return web.json_response([])

async def handle_deepseek_models(request: web.Request) -> web.Response:
    """Deepseek模型获取路由处理器"""
    try:
        handler = DeepseekHandler()
        models = await handler.fetch_models()
        return web.json_response(models)
    except Exception as e:
        print(f"Error fetching Deepseek models: {e}")
        return web.json_response([])

async def handle_api_key_validation(request: web.Request) -> web.Response:
    """API密钥验证路由处理器"""
    try:
        data = await request.json()
        provider = data.get('provider')
        api_key = data.get('api_key')
        
        if not provider or not api_key:
            return web.Response(text="缺少必要参数", status=400)
            
        # 更新配置文件
        config_path = os.path.join(PLUGIN_ROOT, "config", "llm_config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 更新对应提供商的API密钥
            if provider == "Silicon Cloud":
                config["silicon_cloud"]["api_key"] = api_key
            elif provider == "Deepseek":
                config["deepseek"]["api_key"] = api_key
                
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            # 验证API密钥
            if provider == "Silicon Cloud":
                handler = SiliconCloudHandler()
            else:
                handler = DeepseekHandler()
                
            is_valid = await handler.validate_api_key(provider)
            
            if is_valid:
                return web.Response(text="API密钥验证成功")
            else:
                return web.Response(text="API密钥验证失败", status=400)
                
        except Exception as e:
            print(f"Error updating config: {e}")
            return web.Response(text=f"配置文件更新失败: {str(e)}", status=500)
            
    except Exception as e:
        print(f"Error validating API key: {e}")
        return web.Response(text=str(e), status=500) 
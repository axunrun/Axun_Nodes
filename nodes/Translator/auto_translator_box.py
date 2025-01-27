"""
Auto Translator Box Node for ComfyUI
提供自动翻译功能的文本框节点
"""

import os
import json
import re
import asyncio
from typing import Dict, Any
from server import PromptServer
from aiohttp import web
from .utils.translator_utils import handle_translate_text, is_chinese, translate_with_baidu, load_translator_config

# 存储节点实例的翻译文本
translated_texts = {}

@PromptServer.instance.routes.get("/axun-translator/get-translation")
async def get_translation(request):
    """获取翻译文本"""
    node_id = request.query.get("id")
    if not node_id:
        return web.Response(status=400)
    return web.json_response({"translated_text": translated_texts.get(node_id, "")})

class AutoTranslatorBox:
    """自动翻译文本框节点"""
    
    def __init__(self):
        print("[AutoTranslatorBox] 初始化自动翻译文本框节点...")
        self.config = load_translator_config()
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
                "translated": ("STRING", {"multiline": True, "default": "翻译结果将显示在这里...", "readonly": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process_text"
    CATEGORY = "!Axun Nodes/Translator"
    OUTPUT_NODE = True
    
    async def _translate_text(self, text: str, appid: str, key: str, from_lang: str, to_lang: str) -> str:
        """异步执行翻译"""
        try:
            return await translate_with_baidu(text, appid, key, from_lang, to_lang)
        except Exception as e:
            print(f"[AutoTranslatorBox] 翻译失败: {e}")
            return ""
    
    def process_text(self, text: str, translated: str, unique_id: str) -> tuple[str]:
        """
        处理输入文本并自动翻译
        Args:
            text: 输入的文本
            translated: 翻译结果显示区域（只读）
            unique_id: 节点唯一标识
        Returns:
            tuple: (原文,)
        """
        print(f"[AutoTranslatorBox] 开始处理文本: {text[:100]}...")
        if not text.strip():
            print("[AutoTranslatorBox] 文本为空，跳过翻译")
            return (text,)
            
        try:
            # 检测语言
            first_paragraph = text.split('\n')[0]
            is_chinese_text = is_chinese(first_paragraph)
            print(f"[AutoTranslatorBox] 检测到{'中' if is_chinese_text else '英'}文")
            
            # 加载配置
            config = load_translator_config()
            appid = config["baidu_api"]["appid"]
            key = config["baidu_api"]["key"]
            
            if not appid or not key:
                print("[AutoTranslatorBox] API配置缺失")
                return (text,)
            
            print("[AutoTranslatorBox] 开始调用百度翻译API...")
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 执行翻译
            translated = loop.run_until_complete(
                self._translate_text(
                    text,
                    appid,
                    key,
                    "zh" if is_chinese_text else "en",
                    "en" if is_chinese_text else "zh"
                )
            )
            
            # 关闭事件循环
            loop.close()
            
            # 返回结果
            if translated:
                print(f"[AutoTranslatorBox] 翻译完成: {translated[:100]}...")
                # 通知前端更新翻译结果
                PromptServer.instance.send_sync(
                    "impact-node-feedback",
                    {
                        "node_id": unique_id,
                        "widget_name": "translated",
                        "type": "string",
                        "value": translated
                    }
                )
                return (text,)
            else:
                print("[AutoTranslatorBox] 翻译返回空结果")
                return (text,)
            
        except Exception as e:
            print(f"[AutoTranslatorBox] 处理失败: {str(e)}")
            return (text,) 
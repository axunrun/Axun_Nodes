"""
Translator Node for ComfyUI
提供文本翻译功能的节点
"""

import os
import json
import re
import asyncio
from typing import Dict, Any
from server import PromptServer
from .utils.translator_utils import handle_translate_text, is_chinese, translate_with_baidu, load_translator_config

class TranslatorNode:
    """翻译器节点类"""
    
    def __init__(self):
        print("[Translator] 初始化翻译节点...")
        self.config = load_translator_config()
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "translate"
    CATEGORY = "!Axun Nodes/Translator"
    
    def translate(self, text: str) -> tuple:
        """
        执行翻译操作，自动识别中英文并互译
        支持全文多段落翻译
        Args:
            text: 要翻译的文本
        Returns:
            tuple: 包含翻译后文本的元组
        """
        print(f"[Translator] 开始翻译文本...")
        if not text.strip():
            print("[Translator] 文本为空，跳过翻译")
            return (text,)
            
        # 使用工具函数检测第一段文本的语言
        first_paragraph = text.split('\n')[0]
        is_chinese_text = is_chinese(first_paragraph)
        print(f"[Translator] 检测到{'中' if is_chinese_text else '英'}文")
        
        try:
            config = load_translator_config()
            appid = config["baidu_api"]["appid"]
            key = config["baidu_api"]["key"]
            
            if not appid or not key:
                print("[Translator] API配置缺失")
                return (text,)
            
            print("[Translator] 开始调用百度翻译API...")
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 在新的事件循环中运行异步函数
            result = loop.run_until_complete(
                translate_with_baidu(
                    text, 
                    appid, 
                    key,
                    "zh" if is_chinese_text else "en",
                    "en" if is_chinese_text else "zh"
                )
            )
            
            # 关闭事件循环
            loop.close()
            
            print(f"[Translator] 翻译完成")
            return (result,)
        except Exception as e:
            print(f"[Translator] 翻译失败: {e}")
            return (text,)
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        return load_translator_config() 
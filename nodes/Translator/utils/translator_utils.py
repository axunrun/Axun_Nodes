"""
翻译工具函数
提供翻译功能的核心实现
"""

import os
import json
import hashlib
import random
import requests
from aiohttp import web
from server import PromptServer

def load_translator_config():
    """
    读取翻译器配置
    来源：Translator 节点组
    用途：加载百度翻译 API 配置
    """
    # 从插件根目录的config读取
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "config", "translator.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except:
        return {"baidu_api": {"appid": "", "key": ""}}

def is_chinese(text):
    """
    检查文本是否包含中文
    来源：Translator 节点组
    用途：判断文本语言类型
    """
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

async def translate_with_baidu(text, appid, key, from_lang, to_lang):
    """
    使用百度翻译API进行翻译
    来源：Translator 节点组
    用途：调用百度翻译 API
    """
    url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + key).encode()).hexdigest()
    
    params = {
        'appid': appid,
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'salt': salt,
        'sign': sign
    }
    
    try:
        response = requests.get(url, params=params)
        result = response.json()
        
        if 'trans_result' in result:
            translated = result['trans_result'][0]['dst']
            return translated
        else:
            error_msg = result.get('error_msg', 'Unknown error')
            raise Exception(f"Translation error: {error_msg}")
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")

@PromptServer.instance.routes.post('/translator/translate')
async def handle_translate_text(request):
    """
    翻译请求处理函数
    来源：Translator 节点组
    用途：处理翻译请求
    """
    try:
        data = await request.json()
        text = data.get("text", "")
        config = load_translator_config()
        
        appid = config["baidu_api"]["appid"]
        key = config["baidu_api"]["key"]
        
        if not text or not appid or not key:
            return web.json_response({"error": "Missing required parameters"}, status=400)
        
        if is_chinese(text):
            translated = await translate_with_baidu(text, appid, key, 'zh', 'en')
        else:
            translated = await translate_with_baidu(text, appid, key, 'en', 'zh')
            
        return web.json_response({"translated": translated})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500) 
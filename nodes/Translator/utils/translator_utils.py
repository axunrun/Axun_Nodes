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
import asyncio

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
    支持：全文多段落翻译
    """
    url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
    salt = str(random.randint(32768, 65536))
    
    # 分割文本为段落
    paragraphs = text.split('\n')
    translated_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            translated_paragraphs.append('')
            continue
            
        # 为每个段落生成新的签名
        sign = hashlib.md5((appid + paragraph + salt + key).encode()).hexdigest()
        
        params = {
            'appid': appid,
            'q': paragraph,
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
                translated_paragraphs.append(translated)
            else:
                error_msg = result.get('error_msg', 'Unknown error')
                raise Exception(f"Translation error: {error_msg}")
                
            # 添加延时避免请求过快
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"翻译段落时出错: {str(e)}")
            # 如果翻译失败，保留原文
            translated_paragraphs.append(paragraph)
    
    # 使用原始文本的换行方式重新组合
    return '\n'.join(translated_paragraphs)

@PromptServer.instance.routes.post('/translator/translate')
async def handle_translate_text(request):
    """
    翻译请求处理函数
    来源：Translator 节点组
    用途：处理翻译请求
    支持：全文多段落翻译
    """
    try:
        data = await request.json()
        text = data.get("text", "")
        config = load_translator_config()
        
        appid = config["baidu_api"]["appid"]
        key = config["baidu_api"]["key"]
        
        if not text or not appid or not key:
            return web.json_response({"error": "Missing required parameters"}, status=400)
        
        # 检测第一段文本的语言类型
        first_paragraph = text.split('\n')[0]
        is_source_chinese = is_chinese(first_paragraph)
        
        translated = await translate_with_baidu(
            text, 
            appid, 
            key,
            'zh' if is_source_chinese else 'en',
            'en' if is_source_chinese else 'zh'
        )
            
        return web.json_response({"translated": translated})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500) 
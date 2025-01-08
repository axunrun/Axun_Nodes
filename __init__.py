import importlib.util
import sys
import logging
import os
import json
import hashlib
import random
import requests
from aiohttp import web
from server import PromptServer

# 配置日志
def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def install_tkinter():
    """安装tkinter"""
    try:
        importlib.import_module('tkinter')
    except ImportError:
        print("[AxunNodes] 正在尝试安装tkinter")
        try:
            import subprocess
            import platform
            system = platform.system()
            if system == 'Darwin':
                result = subprocess.run(['brew', 'install', 'python-tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Brew安装失败，请确保已安装brew (https://brew.sh/)")
            elif system == 'Linux':
                result = subprocess.run(['sudo', 'apt', '-y', 'install', 'python3-tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Apt安装失败")
            else:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Pip安装失败")
        except Exception as e:
            print("[AxunNodes] 无法安装tkinter，请尝试设置TCL_LIBRARY和TK_LIBRARY环境变量")
            print(e)

# 初始化
setup_logging()
install_tkinter()

# 导入节点
from .nodes.Qtools.path_processor import PathProcessor
from .nodes.Qtools.queue_trigger import ImpactQueueTriggerCountdown
from .nodes.Qtools.work_mode import WorkMode
from .nodes.Qtools.dir_picker import DirPicker, dir_api

# 导入 SUPIR 节点
from .nodes.Supir.supir_sample import SUPIR_sample
from .nodes.Supir.supir_first_stage import SUPIR_first_stage
from .nodes.Supir.supir_encode import SUPIR_encode
from .nodes.Supir.supir_decode import SUPIR_decode
from .nodes.Supir.supir_conditioner import SUPIR_conditioner
from .nodes.Supir.supir_model_loader import SUPIR_model_loader

# 翻译功能相关导入
from .nodes.Translator.translator_node import TranslatorNode

# Web目录
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

# 节点映射
NODE_CLASS_MAPPINGS = {
    "axun_nodes_PathProcessor": PathProcessor,
    "axun_nodes_QueueTrigger": ImpactQueueTriggerCountdown,
    "axun_nodes_WorkMode": WorkMode,
    "axun_nodes_DirPicker": DirPicker,
    # SUPIR 节点
    "SUPIR_sample": SUPIR_sample,
    "SUPIR_first_stage": SUPIR_first_stage,
    "SUPIR_encode": SUPIR_encode,
    "SUPIR_decode": SUPIR_decode,
    "SUPIR_conditioner": SUPIR_conditioner,
    "SUPIR_model_loader": SUPIR_model_loader,
    "TranslatorNode": TranslatorNode
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "axun_nodes_PathProcessor": "Path Processor",
    "axun_nodes_QueueTrigger": "Queue Trigger",
    "axun_nodes_WorkMode": "Work Mode",
    "axun_nodes_DirPicker": "Directory Picker",
    # SUPIR 节点
    "SUPIR_sample": "SUPIR Sampler",
    "SUPIR_first_stage": "SUPIR First Stage (Denoiser)",
    "SUPIR_encode": "SUPIR Encode",
    "SUPIR_decode": "SUPIR Decode",
    "SUPIR_conditioner": "SUPIR Conditioner",
    "SUPIR_model_loader": "SUPIR Model Loader",
    "TranslatorNode": "Translator"
}

# 读取配置文件
def load_translator_config():
    config_path = os.path.join(os.path.dirname(__file__), "config", "translator.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"baidu_api": {"appid": "", "key": ""}}

def is_chinese(text):
    """检查文本是否包含中文"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

async def translate_with_baidu(text, appid, key, from_lang, to_lang):
    """使用百度翻译API进行翻译"""
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
            return result['trans_result'][0]['dst']
        else:
            raise Exception(f"Translation error: {result.get('error_msg', 'Unknown error')}")
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")

# 注册翻译API路由
@PromptServer.instance.routes.post('/translator/translate')
async def translate_text(request):
    try:
        data = await request.json()
        text = data.get("text", "")
        config = load_translator_config()
        
        # 获取API密钥
        appid = config["baidu_api"]["appid"]
        key = config["baidu_api"]["key"]
        
        if not text or not appid or not key:
            return web.json_response({"error": "Missing required parameters"}, status=400)
        
        # 检测语言并翻译
        if is_chinese(text):
            translated = await translate_with_baidu(text, appid, key, 'zh', 'en')
        else:
            translated = await translate_with_baidu(text, appid, key, 'en', 'zh')
            
        return web.json_response({"translated": translated})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

print(f"\033[92mTranslator Plugin loaded.\033[0m")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'dir_api']
VERSION = "1.01"  # 更新版本号
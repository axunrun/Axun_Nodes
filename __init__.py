# 版本信息
VERSION = "1.05"

import os
import sys
import json
import platform
import subprocess
import importlib
from typing import Dict, Any
from aiohttp import web
from server import PromptServer

# Web目录定义
WEB_DIRECTORY = "./web"

#######################
# Qtools 节点组
#######################
def install_tkinter():
    """安装tkinter依赖"""
    try:
        importlib.import_module('tkinter')
    except ImportError:
        print("[AxunNodes] 正在尝试安装tkinter")
        try:
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

# 确保tkinter已安装
install_tkinter()

#######################
# 导入所有节点
#######################

# Qtools节点组
from .nodes.Qtools.dir_picker import DirPicker
from .nodes.Qtools.path_processor import PathProcessor
from .nodes.Qtools.queue_trigger import ImpactQueueTriggerCountdown
from .nodes.Qtools.work_mode import WorkMode

# AI助手节点组
from .nodes.AIAssistant.AIAssistant import SiliconCloudLLMAPI, SiliconCloudVLMAPI, DeepSeekLLMAPI
from .nodes.AIAssistant.preset_node import AIAssistantPreset
from .nodes.AIAssistant.text_processor import TextProcessor
from .nodes.AIAssistant.number_generator import NumberGenerator
from .nodes.AIAssistant.text_cache import TextCache
from .nodes.AIAssistant.text_selector import TextSelector
from .nodes.AIAssistant.image_selector import ImageSelector

# 翻译节点组
from .nodes.Translator.translator_node import TranslatorNode
from .nodes.Translator.auto_translator_box import AutoTranslatorBox

# Lotus节点组
from .nodes.Lotus.lotus_nodes import LoadLotusModel, LotusSampler

# SUPIR节点组
from .nodes.Supir.supir_sample import SUPIR_sample
from .nodes.Supir.supir_first_stage import SUPIR_first_stage
from .nodes.Supir.supir_encode import SUPIR_encode
from .nodes.Supir.supir_decode import SUPIR_decode
from .nodes.Supir.supir_conditioner import SUPIR_conditioner
from .nodes.Supir.supir_model_loader import SUPIR_model_loader

#######################
# 节点映射
#######################

# 节点类映射
NODE_CLASS_MAPPINGS = {
    # Qtools节点组
    "axun_nodes_DirPicker": DirPicker,
    "axun_nodes_PathProcessor": PathProcessor,
    "axun_nodes_QueueTrigger": ImpactQueueTriggerCountdown,
    "axun_nodes_WorkMode": WorkMode,
    
    # AI助手节点组
    "SiliconCloudLLMAPI": SiliconCloudLLMAPI,
    "SiliconCloudVLMAPI": SiliconCloudVLMAPI,
    "DeepSeekLLMAPI": DeepSeekLLMAPI,
    "AIAssistantPreset": AIAssistantPreset,
    "TextProcessor": TextProcessor,
    "NumberGenerator": NumberGenerator,
    "TextCache": TextCache,
    "TextSelector": TextSelector,
    "ImageSelector": ImageSelector,
    
    # 翻译节点组
    "TranslatorNode": TranslatorNode,
    "AutoTranslatorBox": AutoTranslatorBox,
    
    # Lotus节点组
    "LoadLotusModel": LoadLotusModel,
    "LotusSampler": LotusSampler,
    
    # SUPIR节点组
    "SUPIR_sample": SUPIR_sample,
    "SUPIR_first_stage": SUPIR_first_stage,
    "SUPIR_encode": SUPIR_encode,
    "SUPIR_decode": SUPIR_decode,
    "SUPIR_conditioner": SUPIR_conditioner,
    "SUPIR_model_loader": SUPIR_model_loader
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    # Qtools节点组
    "axun_nodes_DirPicker": "📁 Directory Picker",
    "axun_nodes_PathProcessor": "🔍 Path Processor",
    "axun_nodes_QueueTrigger": "⏱️ Queue Trigger",
    "axun_nodes_WorkMode": "⚙️ Work Mode",
    
    # AI助手节点组
    "SiliconCloudLLMAPI": "🤖 Silicon Cloud LLM",
    "SiliconCloudVLMAPI": "🔍 Silicon Cloud VLM",
    "DeepSeekLLMAPI": "🤖 DeepSeek LLM",
    "AIAssistantPreset": "⚙️ AI Assistant Preset",
    "TextProcessor": "📝 Text Processor",
    "NumberGenerator": "🔢 Number Generator",
    "TextCache": "📝 Text Cache",
    "TextSelector": "🔀 Text Selector",
    "ImageSelector": "🔄 Image Selector",
    
    # 翻译节点组
    "TranslatorNode": "🌐 Translator",
    "AutoTranslatorBox": "📝 Auto Translator Box",
    
    # Lotus节点组
    "LoadLotusModel": "🧠 Load Lotus Model",
    "LotusSampler": "✨ Lotus Sampler",
    
    # SUPIR节点组
    "SUPIR_sample": "🎨 SUPIR Sampler",
    "SUPIR_first_stage": "🖼️ SUPIR First Stage",
    "SUPIR_encode": "📥 SUPIR Encode",
    "SUPIR_decode": "📤 SUPIR Decode",
    "SUPIR_conditioner": "🔧 SUPIR Conditioner",
    "SUPIR_model_loader": "💾 SUPIR Model Loader"
}

#######################
# 初始化完成
#######################

print(f"\033[92mAxun Nodes Plugin v{VERSION} loaded.\033[0m")

# 导出必要的变量
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
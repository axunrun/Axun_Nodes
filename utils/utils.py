import json
import os
from typing import Dict

def load_config(config_name: str) -> Dict:
    """
    加载配置文件
    被以下节点引用:
    - AIAssistant/llm_node.py
    
    Args:
        config_name: 配置文件名称(不含路径)
        
    Returns:
        配置字典
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             "config", config_name)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config {config_name}: {e}")
        return {}

def init_config(config_name: str, default_config: Dict) -> None:
    """
    初始化配置文件
    被以下节点引用:
    - AIAssistant/llm_node.py
    - Translator/translator_node.py
    
    Args:
        config_name: 配置文件名称
        default_config: 默认配置内容
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             "config", config_name)
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)

def get_api_key(config_name: str, provider: str) -> str:
    """
    获取指定服务商的 API Key
    被以下节点引用:
    - AIAssistant/llm_node.py
    
    Args:
        config_name: 配置文件名称
        provider: 服务提供商名称
        
    Returns:
        API Key字符串
    """
    config = load_config(config_name)
    return config.get(provider, {}).get("api_key", "") 
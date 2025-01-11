"""
配置相关工具函数
用途：处理配置文件的初始化和管理
"""

import os
import json
import logging
from typing import Dict, Any
from .utils import init_config

logger = logging.getLogger("axun_nodes.config")

# 获取当前模块所在目录
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(UTILS_DIR)

# 全局变量存储所有节点的prompts
node_prompts = {}

def get_default_prompts() -> Dict[str, Dict[str, str]]:
    """获取默认的prompt预设"""
    return {
        "Silicon Cloud LLM": {
            "system": "你是一个 stable diffusion prompt 专家，为我生成适用于 Stable Diffusion 模型的prompt。 我给你相关的单词，你帮我扩写为适合 Stable Diffusion 文生图的 prompt。要求： 1. 英文输出 2. 除了 prompt 外，不要输出任何其它的信息",
            "user": "梵高风格的小猫"
        },
        "Silicon Cloud VLM": {
            "system": "你是一个能分析图像的AI助手。请仔细观察图像，并根据用户的问题提供详细、准确的描述。",
            "user": "请描述这张图片的内容，并指出任何有趣或不寻常的细节。"
        },
        "Deepseek": {
            "system": "你是一个 stable diffusion prompt 专家，为我生成适用于 Stable Diffusion 模型的prompt。 我给你相关的单词，你帮我扩写为适合 Stable Diffusion 文生图的 prompt。要求： 1. 英文输出 2. 除了 prompt 外，不要输出任何其它的信息",
            "user": "梵高风格的小猫"
        }
    }

def init_all_configs() -> None:
    """
    初始化所有配置文件
    包括：
    - LLM配置
    - 翻译配置
    - Prompt预设
    """
    # 确保配置目录存在
    config_dir = os.path.join(PLUGIN_ROOT, "config")
    os.makedirs(config_dir, exist_ok=True)
    
    # LLM配置
    init_config("llm_config.json", {
        "silicon_cloud": {
            "api_key": "",
            "base_url": "https://api.siliconflow.cn/v1"
        },
        "deepseek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1"
        }
    })
    
    # 翻译配置
    init_config("translator.json", {
        "baidu_api": {
            "appid": "",
            "key": ""
        }
    })
    
    # Prompt预设配置
    prompts_path = os.path.join(config_dir, "llm_prompts.json")
    if not os.path.exists(prompts_path):
        with open(prompts_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        logger.info("创建了新的prompt预设配置文件")
    
    # 加载所有节点的prompts
    load_all_prompts()

def get_prompts_file_path() -> str:
    """获取prompts配置文件路径"""
    return os.path.join(PLUGIN_ROOT, "config", "llm_prompts.json")

def load_all_prompts() -> None:
    """加载所有节点的prompt预设"""
    try:
        config_path = get_prompts_file_path()
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                node_prompts.clear()
                # 兼容旧格式
                if isinstance(data, dict):
                    if 'prompts' in data:
                        node_prompts.update(data['prompts'])
                    else:
                        node_prompts.update(data)
                logger.info("成功加载所有节点的prompt预设")
    except Exception as e:
        logger.error(f"加载prompt预设失败: {e}")

def save_all_prompts() -> None:
    """保存所有节点的prompt预设"""
    try:
        config_path = get_prompts_file_path()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(node_prompts, f, indent=4, ensure_ascii=False)
        logger.info("成功保存所有节点的prompt预设")
    except Exception as e:
        logger.error(f"保存prompt预设失败: {e}")

def load_prompts(node_id: str) -> Dict[str, Dict[str, str]]:
    """
    加载指定节点的prompt预设
    Args:
        node_id: 节点ID
    Returns:
        Dict: 节点的prompt预设，如果不存在则返回默认值
    """
    if node_id not in node_prompts:
        node_prompts[node_id] = get_default_prompts()
    return node_prompts[node_id]

def save_prompts(node_id: str, prompts: Dict[str, Dict[str, str]]) -> None:
    """
    保存指定节点的prompt预设
    Args:
        node_id: 节点ID
        prompts: 要保存的prompt预设
    """
    node_prompts[node_id] = prompts
    save_all_prompts()

def delete_node_prompts(node_id: str) -> None:
    """
    删除节点的prompt预设
    Args:
        node_id: 要删除的节点ID
    """
    try:
        if node_id in node_prompts:
            node_prompts.pop(node_id)
            save_all_prompts()
            logger.info(f"删除了节点 {node_id} 的预设")
    except Exception as e:
        logger.error(f"删除节点 {node_id} 的预设失败: {e}") 
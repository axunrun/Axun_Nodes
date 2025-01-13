"""
配置管理器
"""

import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join("config", "silicon_config.json")
        self._config = None

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        if self._config is None:
            self._load_config()
        return self._config

    def _load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                self._create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._get_default_config()

    def _create_default_config(self):
        """创建默认配置文件"""
        config = self._get_default_config()
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "silicon_cloud": {
                "api_key": "",
                "base_url": "https://api.siliconflow.cn/v1",
                "models_endpoint": "/models"
            },
            "parameters": {
                "llm": {
                    "default_system_prompt": "你是一个 stable diffusion prompt 专家，为我生成适用于 Stable Diffusion 模型的prompt。 我给你相关的单词，你帮我扩写为适合 Stable Diffusion 文生图的 prompt。要求： 1. 英文输出 2. 除了 prompt 外，不要输出任何其它的信息",
                    "max_tokens": 512,
                    "temperature": 0.7
                },
                "vlm": {
                    "default_system_prompt": "你是一个能分析图像的AI助手。请仔细观察图像，并根据用户的问题提供详细、准确的描述。",
                    "max_tokens": 512,
                    "temperature": 0.7
                }
            }
        }

    def save_config(self, config: Dict[str, Any]):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self._config = config
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_api_key(self, api_key: str):
        """更新API密钥"""
        config = self.get_config()
        config["silicon_cloud"]["api_key"] = api_key
        self.save_config(config) 
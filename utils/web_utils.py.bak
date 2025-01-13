"""
Web相关工具函数
用途：处理Web文件注册和相关功能
"""

import os
from aiohttp import web
from typing import Dict

def register_js_files(web_directory: str, prompt_server) -> None:
    """
    注册 JavaScript 文件
    Args:
        web_directory: Web文件目录路径
        prompt_server: PromptServer实例
    """
    # Web目录中的文件（不包含已迁移到节点目录的文件）
    js_files: Dict[str, str] = {
        "web.js": "text/javascript",
        "llm.js": "text/javascript",
        "translator.js": "text/javascript"
    }
    
    # 注册文件
    for filename, mime_type in js_files.items():
        file_path = os.path.join(web_directory, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                prompt_server.app.router.add_get(
                    f"/axun_nodes/{filename}",
                    lambda _: web.Response(text=content, content_type=mime_type)
                ) 
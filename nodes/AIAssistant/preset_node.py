import json
import os
from server import PromptServer
from aiohttp import web

class AIAssistantPreset:
    @classmethod
    def get_config_path(cls):
        """获取配置文件路径"""
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"[AIAssistant] 当前文件目录: {current_dir}")
        
        # 获取Axun_Nodes目录（当前文件上溯两级）
        axun_nodes_dir = os.path.dirname(os.path.dirname(current_dir))
        print(f"[AIAssistant] Axun_Nodes目录: {axun_nodes_dir}")
        
        # 构建配置文件路径
        config_path = os.path.join(axun_nodes_dir, "config", "AIAssistant_presets.json")
        print(f"[AIAssistant] 配置文件完整路径: {os.path.abspath(config_path)}")
        
        # 检查文件是否存在
        if os.path.exists(config_path):
            print(f"[AIAssistant] 配置文件已存在")
        else:
            print(f"[AIAssistant] 配置文件不存在")
        
        return config_path

    @classmethod
    def load_presets(cls):
        """加载预设配置"""
        try:
            config_path = cls.get_config_path()
            
            if not os.path.exists(config_path):
                print(f"[AIAssistant] 配置文件不存在，将创建默认配置")
                default_config = {
                    "system_presets": {
                        "null": {
                            "system_prompt": "",
                            "temperature": 0.7,
                            "top_p": 0.9
                        },
                        "通用场景": {
                            "system_prompt": "You are an AI assistant specialized in creating high-quality image generation prompts. Please provide detailed and creative descriptions that work well with Stable Diffusion.",
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    },
                    "style_presets": {
                        "null": {"prompt": ""},
                        "写实风格": {"prompt": "photorealistic, highly detailed, 8k uhd, high quality, masterpiece, professional photography, sharp focus"}
                    },
                    "shot_presets": {
                        "null": {"prompt": ""},
                        "特写镜头": {"prompt": "close-up shot, detailed facial features, shallow depth of field, bokeh effect, portrait composition"}
                    },
                    "character_presets": {
                        "null": {"prompt": ""},
                        "冒险家": {"prompt": "adventurous explorer, rugged appearance, determined expression, weathered clothing, exploration gear, dynamic pose"},
                        "智者": {"prompt": "wise scholar, sophisticated appearance, thoughtful expression, elegant clothing, academic attire, dignified pose"},
                        "机器人": {"prompt": "advanced android, sleek metallic surface, glowing interface, precise mechanical details, robotic features, high-tech design"},
                        "魔法师": {"prompt": "powerful mage, ornate robes, mystical artifacts, glowing magical effects, arcane symbols, dramatic lighting"}
                    }
                }
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                cls.save_presets(default_config)
                return default_config
            
            with open(config_path, 'r', encoding='utf-8') as f:
                presets = json.loads(f.read())
            return presets
        except Exception as e:
            print(f"[AIAssistant] 加载预设配置失败: {e}")
            return cls.get_default_config()

    @classmethod
    def save_presets(cls, presets):
        """保存预设到文件"""
        try:
            config_path = cls.get_config_path()
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 先将内容转换为JSON字符串
            content = json.dumps(presets, ensure_ascii=False, indent=4)
            print(f"[AIAssistant] 准备写入的内容: {content}")
            
            # 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[AIAssistant] 预设保存成功，当前预设: {list(presets.keys())}")
            
            # 验证写入是否成功
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    verify_content = f.read()
                print(f"[AIAssistant] 验证读取的内容: {verify_content}")
            
            return True
        except Exception as e:
            print(f"[AIAssistant] 保存预设失败: {e}")
            return False

    @classmethod
    def get_default_config(cls):
        """获取默认配置"""
        return {
            "system_presets": {
                "null": {
                    "system_prompt": "",
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "通用场景": {
                    "system_prompt": "You are an AI assistant specialized in creating high-quality image generation prompts. Please provide detailed and creative descriptions that work well with Stable Diffusion.",
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            "style_presets": {
                "null": {"prompt": ""},
                "写实风格": {"prompt": "photorealistic, highly detailed, 8k uhd, high quality, masterpiece, professional photography, sharp focus"}
            },
            "shot_presets": {
                "null": {"prompt": ""},
                "特写镜头": {"prompt": "close-up shot, detailed facial features, shallow depth of field, bokeh effect, portrait composition"}
            },
            "character_presets": {
                "null": {"prompt": ""},
                "冒险家": {"prompt": "adventurous explorer, rugged appearance, determined expression, weathered clothing, exploration gear, dynamic pose"},
                "智者": {"prompt": "wise scholar, sophisticated appearance, thoughtful expression, elegant clothing, academic attire, dignified pose"},
                "机器人": {"prompt": "advanced android, sleek metallic surface, glowing interface, precise mechanical details, robotic features, high-tech design"},
                "魔法师": {"prompt": "powerful mage, ornate robes, mystical artifacts, glowing magical effects, arcane symbols, dramatic lighting"}
            }
        }

    @classmethod
    def INPUT_TYPES(s):
        """获取输入类型"""
        try:
            presets = s.load_presets()
            # 确保所有预设类型都存在
            if not all(key in presets for key in ["system_presets", "style_presets", "shot_presets", "character_presets"]):
                print("[AIAssistant] 预设配置不完整，使用默认配置")
                presets = s.get_default_config()

            # 获取角色预设列表
            character_presets = list(presets.get("character_presets", {}).keys())
            
            return {
                "required": {
                    "system_preset": (list(presets.get("system_presets", {}).keys()),),
                    "custom_system": ("STRING", {"multiline": True}),
                    "style_preset": (list(presets.get("style_presets", {}).keys()),),
                    "shot_preset": (list(presets.get("shot_presets", {}).keys()),),
                    "character_a_preset": (character_presets,),
                    "character_b_preset": (character_presets,),
                    "character_c_preset": (character_presets,),
                    "custom_prompt": ("STRING", {"multiline": True}),
                    "seed_mode": (["fixed", "increment", "decrement", "randomize"],),
                    "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                }
            }
        except Exception as e:
            print(f"[AIAssistant] INPUT_TYPES加载失败: {e}")
            # 使用默认配置
            default_config = s.get_default_config()
            character_presets = list(default_config["character_presets"].keys())
            return {
                "required": {
                    "system_preset": (list(default_config["system_presets"].keys()),),
                    "custom_system": ("STRING", {"multiline": True}),
                    "style_preset": (list(default_config["style_presets"].keys()),),
                    "shot_preset": (list(default_config["shot_presets"].keys()),),
                    "character_a_preset": (character_presets,),
                    "character_b_preset": (character_presets,),
                    "character_c_preset": (character_presets,),
                    "custom_prompt": ("STRING", {"multiline": True}),
                    "seed_mode": (["fixed", "increment", "decrement", "randomize"],),
                    "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff})
                }
            }

    RETURN_TYPES = ("STRING", "STRING", "FLOAT", "FLOAT", "INT")
    RETURN_NAMES = ("system_prompt", "user_prompt", "temperature", "top_p", "seed")
    FUNCTION = "apply_preset"
    OUTPUT_NODE = True
    CATEGORY = "!Axun Nodes/AIAssistant"

    def apply_preset(self, system_preset, custom_system, style_preset, shot_preset, 
                    character_a_preset, character_b_preset, character_c_preset, 
                    custom_prompt, seed_mode, seed):
        """应用预设配置并组合输出"""
        presets = self.load_presets()
        
        # 获取系统预设
        system_config = presets["system_presets"].get(system_preset, {})
        system_prompt = system_config.get("system_prompt", "")
        temperature = system_config.get("temperature", 0.7)
        top_p = system_config.get("top_p", 0.9)
        
        # 组合用户提示词
        prompt_parts = []
        
        # 添加风格预设和自定义风格
        style_prompt = presets["style_presets"].get(style_preset, {}).get("prompt", "").strip()
        custom_style_text = custom_system.strip()
        
        if style_preset != "null" or custom_style_text:
            style_parts = []
            if style_preset != "null" and style_prompt:
                style_parts.append(style_prompt)
            if custom_style_text:
                style_parts.append(custom_style_text)
            prompt_parts.append(f"Style: {', '.join(style_parts)}")
        
        # 添加镜头预设
        if shot_preset != "null":
            shot_prompt = presets["shot_presets"].get(shot_preset, {}).get("prompt", "")
            if shot_prompt:
                prompt_parts.append(f"Camera: {shot_prompt}")
        
        # 添加角色预设
        character_presets = presets.get("character_presets", {})
        for preset_name, role_prefix in [
            (character_a_preset, "Character A"),
            (character_b_preset, "Character B"),
            (character_c_preset, "Character C")
        ]:
            if preset_name != "null":
                char_prompt = character_presets.get(preset_name, {}).get("prompt", "")
                if char_prompt:
                    prompt_parts.append(f"{role_prefix}: {char_prompt}")
        
        # 添加自定义提示词（直接添加原文）
        if custom_prompt.strip():
            prompt_parts.append(custom_prompt.strip())
        
        # 组合最终用户提示词，使用双换行符分隔段落
        user_prompt = "\n\n".join(prompt_parts) if prompt_parts else ""
        
        # 处理种子值
        final_seed = seed
        
        return (system_prompt, user_prompt, temperature, top_p, final_seed)

# 注册路由处理函数
@PromptServer.instance.routes.post("/axun/AIAssistant/presets")
async def get_presets(request):
    """获取所有预设列表"""
    try:
        presets = AIAssistantPreset.load_presets()
        return web.json_response(presets)
    except Exception as e:
        print(f"[AIAssistant] 获取预设列表失败: {e}")
        return web.json_response({"error": str(e)})

@PromptServer.instance.routes.post("/axun/AIAssistant/save_preset")
async def save_preset(request):
    """保存预设"""
    try:
        data = await request.json()
        preset_type = data.get("type")  # 新增预设类型参数
        preset_name = data.get("name")
        
        if not preset_type or not preset_name:
            raise ValueError("预设类型和名称不能为空")
        
        presets = AIAssistantPreset.load_presets()
        preset_key = f"{preset_type}_presets"
        
        # 检查预设类型是否有效
        if preset_key not in presets:
            raise ValueError(f"无效的预设类型: {preset_type}")
            
        # 检查是否为保护的预设
        if preset_name == "null":
            raise ValueError("不能覆盖null预设")
            
        if preset_type == "system" and preset_name == "通用场景":
            raise ValueError("不能覆盖默认场景预设")
        
        # 保存预设
        if preset_type == "system":
            presets[preset_key][preset_name] = {
                "system_prompt": data.get("system_prompt", ""),
                "temperature": float(data.get("temperature", 0.7)),
                "top_p": float(data.get("top_p", 0.9))
            }
        else:
            presets[preset_key][preset_name] = {
                "prompt": data.get("prompt", "")
            }
        
        if AIAssistantPreset.save_presets(presets):
            return web.json_response({"status": "success"})
        else:
            raise Exception("保存预设失败")
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)})

@PromptServer.instance.routes.post("/axun/AIAssistant/delete_preset")
async def delete_preset(request):
    """删除预设"""
    try:
        data = await request.json()
        preset_type = data.get("type")
        preset_name = data.get("name")
        
        if not preset_type or not preset_name:
            raise ValueError("预设类型和名称不能为空")
        
        presets = AIAssistantPreset.load_presets()
        preset_key = f"{preset_type}_presets"
        
        if preset_key not in presets:
            raise ValueError(f"无效的预设类型: {preset_type}")
        
        if preset_name not in presets[preset_key]:
            raise ValueError(f"预设不存在: {preset_name}")
            
        if preset_name == "null":
            raise ValueError("null预设不能删除")
            
        del presets[preset_key][preset_name]
        
        if AIAssistantPreset.save_presets(presets):
            return web.json_response({"status": "success"})
        else:
            raise Exception("删除预设失败")
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}) 
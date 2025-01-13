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
                # 如果配置文件不存在，创建默认配置
                default_config = {
                    "通用对话": {
                        "system_prompt": "你是一个AI助手，请根据用户的问题提供准确、有帮助的回答。",
                        "user_prompt": "请描述一下...",
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                cls.save_presets(default_config)  # 使用save_presets方法保存
                return default_config
            
            try:
                # 尝试直接读取
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"[AIAssistant] 读取到的配置文件内容: {content}")
                    presets = json.loads(content)
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                print(f"[AIAssistant] UTF-8解码失败，尝试其他编码")
                with open(config_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    print(f"[AIAssistant] GBK解码后的内容: {content}")
                    presets = json.loads(content)
            
            # 验证加载的数据
            if not isinstance(presets, dict):
                raise ValueError("配置文件格式错误，应该是一个字典")
            
            print(f"[AIAssistant] 成功加载预设配置，当前预设: {list(presets.keys())}")
            return presets
        except Exception as e:
            print(f"[AIAssistant] 加载预设配置失败: {e}")
            print(f"[AIAssistant] 将使用默认配置")
            # 返回默认配置
            return {
                "通用对话": {
                    "system_prompt": "你是一个AI助手，请根据用户的问题提供准确、有帮助的回答。",
                    "user_prompt": "请描述一下...",
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }

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
    def INPUT_TYPES(s):
        """获取输入类型"""
        presets = s.load_presets()  # 每次都重新加载
        preset_names = list(presets.keys())
        print(f"[AIAssistant] INPUT_TYPES返回的预设列表: {preset_names}")
        return {
            "required": {
                "preset": (preset_names, ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "FLOAT", "FLOAT")
    RETURN_NAMES = ("system_prompt", "user_prompt", "temperature", "top_p")
    FUNCTION = "apply_preset"
    OUTPUT_NODE = True
    CATEGORY = "!Axun Nodes/AIAssistant"

    def apply_preset(self, preset):
        """应用预设配置"""
        presets = self.load_presets()  # 每次应用时重新加载
        print(f"[AIAssistant] 应用预设 {preset}，当前可用预设: {list(presets.keys())}")
        
        if preset not in presets:
            print(f"[AIAssistant] 预设 {preset} 不存在，使用默认值")
            return ("", "", 0.7, 0.9)
        
        config = presets[preset]
        return (
            config.get("system_prompt", ""),
            config.get("user_prompt", ""),
            config.get("temperature", 0.7),
            config.get("top_p", 0.9)
        )

# 注册路由处理函数
@PromptServer.instance.routes.post("/axun/AIAssistant/presets")
async def get_presets(request):
    """获取预设列表"""
    try:
        presets = AIAssistantPreset.load_presets()  # 每次都重新加载
        preset_names = list(presets.keys())
        print(f"[AIAssistant] API返回预设列表: {preset_names}")
        return web.json_response(preset_names)
    except Exception as e:
        print(f"[AIAssistant] 获取预设列表失败: {e}")
        return web.json_response(["获取预设列表失败"])

@PromptServer.instance.routes.post("/axun/AIAssistant/save_preset")
async def save_preset(request):
    """保存新预设"""
    try:
        data = await request.json()
        preset_name = data.get("name")
        preset_config = {
            "system_prompt": data.get("system_prompt", ""),
            "user_prompt": data.get("user_prompt", ""),
            "temperature": float(data.get("temperature", 0.7)),
            "top_p": float(data.get("top_p", 0.9))
        }
        
        print(f"[AIAssistant] 准备保存预设: {preset_name}")
        print(f"[AIAssistant] 预设内容: {preset_config}")
        
        # 加载当前预设
        presets = AIAssistantPreset.load_presets()
        print(f"[AIAssistant] 当前已有预设: {list(presets.keys())}")
        
        # 更新预设
        presets[preset_name] = preset_config
        
        # 保存到文件
        if AIAssistantPreset.save_presets(presets):
            print(f"[AIAssistant] 预设 {preset_name} 保存成功")
            return web.json_response({"status": "success"})
        else:
            raise Exception("保存预设失败")
    except Exception as e:
        print(f"[AIAssistant] 保存预设失败: {e}")
        return web.json_response({"status": "error", "message": str(e)})

@PromptServer.instance.routes.post("/axun/AIAssistant/delete_preset")
async def delete_preset(request):
    """删除预设"""
    try:
        data = await request.json()
        preset_name = data.get("name")
        
        print(f"[AIAssistant] 准备删除预设: {preset_name}")
        
        # 加载当前预设
        presets = AIAssistantPreset.load_presets()
        print(f"[AIAssistant] 当前已有预设: {list(presets.keys())}")
        
        # 检查预设是否存在
        if preset_name not in presets:
            raise Exception(f"预设 {preset_name} 不存在")
            
        # 检查是否是默认预设
        if preset_name == "通用对话":
            raise Exception("默认预设不能删除")
            
        # 删除预设
        del presets[preset_name]
        
        # 保存到文件
        if AIAssistantPreset.save_presets(presets):
            print(f"[AIAssistant] 预设 {preset_name} 删除成功")
            return web.json_response({"status": "success"})
        else:
            raise Exception("删除预设失败")
    except Exception as e:
        print(f"[AIAssistant] 删除预设失败: {e}")
        return web.json_response({"status": "error", "message": str(e)}) 
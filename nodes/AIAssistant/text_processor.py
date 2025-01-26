import re
import os
import json
from server import PromptServer
from aiohttp import web

text_indices = {}

@PromptServer.instance.routes.get("/axun-text/text-index")
async def get_text_index(request):
    """获取文本索引"""
    node_id = request.query.get("id")
    if not node_id:
        return web.Response(status=400)
    return web.json_response({"text_index": text_indices.get(node_id, 1)})

@PromptServer.instance.routes.post("/axun-text/set-text-index")
async def set_text_index(request):
    """设置文本索引"""
    node_id = request.query.get("id")
    index = request.query.get("index")
    if not node_id or not index:
        return web.Response(status=400)
    try:
        text_indices[node_id] = int(index)
        return web.Response(status=200)
    except ValueError:
        return web.Response(status=400)

def load_character_presets():
    """加载角色预设"""
    try:
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取配置文件路径
        config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config", "AIAssistant_presets.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            presets = json.load(f)
            return list(presets.get("character_presets", {}).keys())
    except Exception as e:
        print(f"[TextProcessor] 加载角色预设失败: {str(e)}")
        return ["null"]

# 添加路由用于获取最新的角色预设列表
@PromptServer.instance.routes.get("/axun-text/character-presets")
async def get_character_presets(request):
    """获取最新的角色预设列表"""
    try:
        presets = load_character_presets()
        return web.json_response({"presets": presets})
    except Exception as e:
        print(f"[TextProcessor] 获取角色预设列表失败: {str(e)}")
        return web.json_response({"presets": ["null"]})

class TextProcessor:
    """文本处理器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        character_presets = load_character_presets()
        return {
            "required": {
                "appstart_text": ("STRING", {"multiline": True, "default": ""}),
                "sample_text": ("STRING", {"multiline": True}),
                "append_text": ("STRING", {"multiline": True, "default": ""}),
                "content_type": ("STRING", {"default": "scene_*,story_*", "multiline": False}),
                "prefix": ("STRING", {"default": ""}),
                "suffix": ("STRING", {"default": ""}),
                "text_index": ("INT", {"default": 1, "min": 1, "max": 999999}),
                "character_a_preset": (character_presets,),
                "character_b_preset": (character_presets,),
                "character_c_preset": (character_presets,),
            },
            "hidden": {
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("scene_text", "story_text", "current_index", "max_scene")
    FUNCTION = "process_text"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def get_character_info(self, preset_name):
        """获取角色预设信息"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config", "AIAssistant_presets.json")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                presets = json.load(f)
                character_info = presets.get("character_presets", {}).get(preset_name, {})
                if character_info and preset_name != "null":
                    return character_info.get("prompt", "")
        except Exception as e:
            print(f"[TextProcessor] 获取角色信息失败: {str(e)}")
        return ""

    def process_text(self, appstart_text: str, sample_text: str, append_text: str, content_type: str, 
                    prefix: str, suffix: str, text_index: int, character_a_preset: str, 
                    character_b_preset: str, character_c_preset: str, id: str):
        """处理文本内容"""
        try:
            print(f"[TextProcessor] 开始处理文本，当前索引: {text_index}")
            
            # 获取选中的角色信息
            selected_characters = []
            for preset_name in [character_a_preset, character_b_preset, character_c_preset]:
                if preset_name != "null":
                    char_info = self.get_character_info(preset_name)
                    if char_info:
                        selected_characters.append(char_info)
                        print(f"[TextProcessor] 添加角色: {preset_name}")

            # 分析文本内容
            # 解析content_type
            content_types = [t.strip() for t in content_type.split(',')]
            print(f"[TextProcessor] 内容类型过滤: {content_types}")
            
            # 构建正则表达式模式
            patterns = []
            for ct in content_types:
                if '*' in ct:
                    # 将 * 转换为正则表达式
                    pattern = ct.replace('*', r'\d+')
                else:
                    pattern = ct
                patterns.append(f"##({pattern}):\s*\{{(.*?)\}}")
            
            print(f"[TextProcessor] 使用的正则模式: {patterns}")
            
            # 查找所有匹配的内容
            all_matches = []
            for pattern in patterns:
                matches = list(re.finditer(pattern, sample_text, re.DOTALL))
                all_matches.extend(matches)
                print(f"[TextProcessor] 模式 {pattern} 找到 {len(matches)} 个匹配")
            
            if not all_matches:
                print(f"[TextProcessor] 未找到任何匹配内容，检查文本格式是否正确")
                print(f"[TextProcessor] 文本样本:\n{sample_text[:500]}")
                return "", "", 1, 1

            # 提取场景和故事内容
            scene_matches = []
            story_matches = []
            for match in all_matches:
                full_match = match.group(1)  # 例如: "scene_1" 或 "story_1"
                if 'scene_' in full_match:
                    scene_matches.append(match)
                elif 'story_' in full_match:
                    story_matches.append(match)
            
            print(f"[TextProcessor] 找到场景数量: {len(scene_matches)}")
            print(f"[TextProcessor] 找到故事数量: {len(story_matches)}")
            
            if not scene_matches:
                print(f"[TextProcessor] 未找到场景内容")
                return "", "", 1, 1

            # 获取最大索引
            def extract_index(match):
                try:
                    # 从完整匹配中提取数字
                    full_match = match.group(1)  # 例如: "scene_1" 或 "story_1"
                    return int(full_match.split('_')[1])
                except Exception as e:
                    print(f"[TextProcessor] 提取索引出错: {str(e)}")
                    return 0

            max_index = max(extract_index(m) for m in scene_matches)
            print(f"[TextProcessor] 最大索引: {max_index}")
            
            # 确保索引在有效范围内
            current_index = ((text_index - 1) % max_index) + 1
            print(f"[TextProcessor] 当前处理索引: {current_index}")
            
            # 获取当前场景内容
            current_scene = None
            current_story = None
            
            for match in scene_matches:
                if extract_index(match) == current_index:
                    current_scene = match.group(2)
                    print(f"[TextProcessor] 找到当前场景: scene_{current_index}")
                    break
                    
            for match in story_matches:
                if extract_index(match) == current_index:
                    current_story = match.group(2)
                    print(f"[TextProcessor] 找到当前故事: story_{current_index}")
                    break

            # 处理场景内容
            scene_text = ""
            story_text = ""
            
            if current_scene:
                # 检查角色是否在当前场景中
                characters_present = ""
                char_match = re.search(r'"characters_present":\s*"([^"]*)"', current_scene)
                if char_match:
                    characters_present = char_match.group(1).lower()
                    print(f"[TextProcessor] 当前场景角色: {characters_present}")
                
                # 添加相关的角色信息
                for char_info in selected_characters:
                    # 从角色信息中提取名字
                    name_match = re.search(r'Character name:[^:]*?:\s*(\w+)', char_info)
                    if name_match:
                        char_name = name_match.group(1)
                        if char_name.lower() in characters_present:
                            print(f"[TextProcessor] 添加角色信息: {char_name}")
                            # 提取角色信息中的大括号内容
                            char_content_match = re.search(r'##[^{]*:\{(.*?)\}', char_info, re.DOTALL)
                            if char_content_match:
                                scene_text += char_content_match.group(1).strip() + "\n\n"
                            else:
                                scene_text += char_info + "\n\n"
                
                # 添加场景内容（只保留大括号内的内容）
                scene_text += current_scene.strip()
            
            # 处理故事内容（只保留大括号内的内容）
            if current_story:
                story_text = current_story.strip()
            
            # 添加前置文本
            if appstart_text:
                # 如果前置文本包含标识符，只保留大括号内的内容
                if '##' in appstart_text:
                    appstart_matches = re.finditer(r'##[^{]*:\{(.*?)\}', appstart_text, re.DOTALL)
                    appstart_text = '\n\n'.join(m.group(1).strip() for m in appstart_matches)
                scene_text = f"{appstart_text}\n{scene_text}"
                story_text = f"{appstart_text}\n{story_text}"
            
            # 添加后置文本
            if append_text:
                # 如果后置文本包含标识符，只保留大括号内的内容
                if '##' in append_text:
                    append_matches = re.finditer(r'##[^{]*:\{(.*?)\}', append_text, re.DOTALL)
                    append_text = '\n\n'.join(m.group(1).strip() for m in append_matches)
                scene_text = f"{scene_text}\n{append_text}"
                story_text = f"{story_text}\n{append_text}"
            
            # 添加前缀和后缀
            scene_text = f"{prefix}{scene_text}{suffix}"
            story_text = f"{prefix}{story_text}{suffix}"
            
            # 计算并保存下一个索引
            next_index = current_index + 1
            if next_index > max_index:
                next_index = 1
            text_indices[id] = next_index
            print(f"[TextProcessor] 设置下一个索引: {next_index}")
            self._update_index(id, next_index)
            
            return scene_text, story_text, current_index, max_index
            
        except Exception as e:
            print(f"[TextProcessor] 处理文本时出错: {str(e)}")
            return "", "", 1, 1

    def _update_index(self, node_id: str, index: int):
        """更新前端显示的索引值"""
        try:
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "text_index",
                    "type": "int",
                    "value": index
                }
            )
        except Exception as e:
            print(f"[TextProcessor] 更新索引失败: {str(e)}") 
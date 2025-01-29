import re
import os
import json
from server import PromptServer
from aiohttp import web
import traceback

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
                "append_text": ("STRING", {"multiline": True, "default": ""}),
                "content_type": ("STRING", {"default": "scene_*,story_*", "multiline": False}),
                "prefix": ("STRING", {"default": ""}),
                "suffix": ("STRING", {"default": ""}),
                "text_index": ("INT", {"default": 1, "min": 1, "max": 999999}),
                "character_a_preset": (character_presets,),
                "character_b_preset": (character_presets,),
                "character_c_preset": (character_presets,),
            },
            "optional": {
                "sample_story": ("STRING", {"multiline": True, "default": ""}),
                "sample_character": ("STRING", {"multiline": True, "default": ""}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ('story_name', 'story_cover', 'story_summary', 'scene_index', 'scene_text', 'story_index', 
                   'story_text_cn', 'story_text_en', 'character_name', 'character_text', 'current_index', 'max_scene')
    INPUT_IS_LIST = False
    OUTPUT_NODE = True
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

    def extract_character_name(self, text: str) -> str:
        """提取角色名称"""
        try:
            print(f"[TextProcessor] 开始提取角色名称，输入文本:\n{text[:200]}...")
            
            # 使用正则表达式匹配 "Character name:" 后面的内容
            # 修改正则表达式以更好地匹配格式
            match = re.search(r'Character name:\s*\n\s*([^:\n]+):\s*([^:\n]+)', text, re.IGNORECASE | re.MULTILINE)
            if match:
                # 获取匹配的文本并处理
                role = match.group(1).strip()  # 例如 "father fox"
                char_name = match.group(2).strip()  # 例如 "Theo"
                print(f"[TextProcessor] 提取到角色类型: {role}, 名字: {char_name}")
                
                # 将空格替换为下划线，并组合
                role = re.sub(r'\s+', '_', role)
                result = f"{role}_{char_name}"
                print(f"[TextProcessor] 生成的角色名称: {result}")
                return result
                
            print("[TextProcessor] 未找到匹配的角色名称格式")
            return ""
        except Exception as e:
            print(f"[TextProcessor] 提取角色名称失败: {str(e)}")
            return ""

    def extract_story_info(self, text: str) -> dict:
        """提取故事信息"""
        try:
            print(f"[TextProcessor] 开始提取故事信息，输入文本长度: {len(text)}")
            
            # 使用精确的正则表达式匹配故事信息
            story_info_pattern = r'##story_info:\s*\{(.*?)\}\s*(?=##|$)'
            story_info_match = re.search(story_info_pattern, text, re.DOTALL)
            
            if story_info_match:
                story_info_text = story_info_match.group(1).strip()
                print(f"[TextProcessor] 找到故事信息块，长度: {len(story_info_text)}")
                
                # 构建完整的JSON字符串
                json_str = "{" + story_info_text + "}"
                
                # 清理JSON文本
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # 移除尾随逗号
                json_str = re.sub(r'[\n\r]+\s*', ' ', json_str)     # 规范化换行和空格
                
                try:
                    story_info = json.loads(json_str)
                    print(f"[TextProcessor] 成功解析故事信息")
                    print(f"[TextProcessor] 标题: {story_info.get('title_en', '')} / {story_info.get('title_cn', '')}")
                    
                    # 验证必要的字段
                    required_fields = ['title_en', 'title_cn', 'summary_en', 'summary_cn', 'cover_prompt']
                    missing_fields = [field for field in required_fields if field not in story_info]
                    if missing_fields:
                        print(f"[TextProcessor] 警告：缺少必要字段: {missing_fields}")
                    
                    return story_info
                except json.JSONDecodeError as je:
                    print(f"[TextProcessor] JSON解析失败: {str(je)}")
                    print(f"[TextProcessor] 尝试解析的文本: {json_str[:200]}")
            else:
                print(f"[TextProcessor] 未找到故事信息块")
            return {}
        except Exception as e:
            print(f"[TextProcessor] 提取故事信息失败: {str(e)}")
            return {}

    def extract_character_text(self, text: str) -> str:
        """提取角色描述文本"""
        try:
            print(f"[TextProcessor] 开始提取角色描述")
            
            # 提取完整的角色信息，包括标题
            full_text = []
            
            # 提取Character name部分
            name_match = re.search(r'Character name:\s*\n([^#]*?)(?=\n\s*Character prompts:|$)', text, re.DOTALL)
            if name_match:
                name_text = name_match.group(1).strip()
                full_text.extend(["Character name:", name_text])
            
            # 提取Character prompts部分
            prompts_match = re.search(r'Character prompts:\s*\n(.*?)(?=\n\s*$|\}|$)', text, re.DOTALL)
            if prompts_match:
                prompts_text = prompts_match.group(1).strip()
                if full_text:  # 如果已经有name部分，添加空行
                    full_text.append("")
                full_text.extend(["Character prompts:", prompts_text])
            
            if full_text:
                character_text = "\n".join(full_text)
                print(f"[TextProcessor] 成功提取角色描述，长度: {len(character_text)}")
                return character_text
            
            print("[TextProcessor] 未找到角色描述")
            return ""
        except Exception as e:
            print(f"[TextProcessor] 提取角色描述失败: {str(e)}")
            return ""

    def process_text(self, appstart_text: str, append_text: str, content_type: str, 
                    prefix: str, suffix: str, text_index: int, 
                    character_a_preset: str, character_b_preset: str, character_c_preset: str,
                    unique_id=None, extra_pnginfo=None, sample_story=None, sample_character=None):
        """处理文本内容"""
        try:
            print(f"[TextProcessor] 开始处理文本，当前索引: {text_index}")
            
            # 处理可选输入
            sample_story = sample_story or ""
            sample_character = sample_character or ""
            
            def remove_leading_spaces(json_str: str) -> str:
                """移除JSON字符串中每行开头的空格"""
                lines = json_str.split('\n')
                cleaned_lines = [line.lstrip() for line in lines]
                return '\n'.join(cleaned_lines)
            
            # 提取角色名称和描述
            character_name = self.extract_character_name(sample_character)
            character_text = self.extract_character_text(sample_character)
            print(f"[TextProcessor] 提取的角色名称: {character_name}")
            print(f"[TextProcessor] 提取的角色描述长度: {len(character_text)}")
            
            # 提取故事信息
            story_info = self.extract_story_info(sample_story)
            story_name = ""
            story_cover = ""
            story_summary = ""
            
            if story_info:
                # 组合故事名称
                title_en = story_info.get("title_en", "")
                title_cn = story_info.get("title_cn", "")
                if title_en and title_cn:
                    story_name = f"{title_en.replace(' ', '_')}_{title_cn}"
                    print(f"[TextProcessor] 生成故事名称: {story_name}")
                
                # 获取封面提示词（仅在text_index=1时）
                if text_index == 1:
                    cover_prompt = story_info.get("cover_prompt", {})
                    if cover_prompt:
                        # 去掉外层大括号和前导空格的封面提示词
                        cover_json = json.dumps(cover_prompt, ensure_ascii=False, indent=2)
                        story_cover = remove_leading_spaces(cover_json[1:-1].strip())
                        print("[TextProcessor] 生成封面提示词")
                    
                    # 获取故事摘要
                    summary_en = story_info.get("summary_en", "")
                    summary_cn = story_info.get("summary_cn", "")
                    if summary_en and summary_cn:
                        summary_dict = {
                            "summary_en": summary_en,
                            "summary_cn": summary_cn
                        }
                        # 去掉外层大括号和前导空格的摘要
                        summary_json = json.dumps(summary_dict, ensure_ascii=False, indent=2)
                        story_summary = remove_leading_spaces(summary_json[1:-1].strip())
                        print("[TextProcessor] 生成故事摘要")
            
            # 获取选中的角色信息
            selected_characters = []
            for preset_name in [character_a_preset, character_b_preset, character_c_preset]:
                if preset_name != "null":
                    char_info = self.get_character_info(preset_name)
                    if char_info:
                        selected_characters.append(char_info)
                        print(f"[TextProcessor] 添加角色: {preset_name}")
            
            # 如果没有故事内容，返回空结果但保留已处理的信息
            if not sample_story.strip():
                return story_name, story_cover, story_summary, "", "", "", "", "", character_name, character_text, text_index, 1
            
            # 分析文本内容
            content_types = [t.strip() for t in content_type.split(',')]
            
            # 构建正则表达式模式
            patterns = []
            for ct in content_types:
                if '*' in ct:
                    pattern = ct.replace('*', r'\d+')
                else:
                    pattern = ct
                patterns.append(f"##({pattern}):\s*\{{(.*?)\}}")
            
            # 查找所有匹配的内容
            all_matches = []
            for pattern in patterns:
                matches = list(re.finditer(pattern, sample_story, re.DOTALL))
                all_matches.extend(matches)
            
            if not all_matches:
                return story_name, story_cover, story_summary, "", "", "", "", "", character_name, character_text, text_index, 1
            
            # 提取场景和故事内容
            scene_matches = []
            story_matches = []
            for match in all_matches:
                full_match = match.group(1)
                if 'scene_' in full_match:
                    scene_matches.append(match)
                elif 'story_' in full_match:
                    story_matches.append(match)
            
            if not scene_matches:
                return story_name, story_cover, story_summary, "", "", "", "", "", character_name, character_text, text_index, 1
            
            # 获取最大索引
            def extract_index(match):
                try:
                    full_match = match.group(1)
                    return int(full_match.split('_')[1])
                except Exception as e:
                    print(f"[TextProcessor] 提取索引出错: {str(e)}")
                    return 0
            
            max_index = max(extract_index(m) for m in scene_matches)
            current_index = ((text_index - 1) % max_index) + 1
            
            # 获取当前场景和故事内容
            scene_index = ""
            story_index = ""
            scene_text = ""
            story_text_cn = ""
            story_text_en = ""
            
            # 处理场景内容
            for match in scene_matches:
                if extract_index(match) == current_index:
                    scene_index = match.group(1)
                    current_scene = match.group(2)
                    
                    # 处理场景内容
                    scene_content = ""
                    
                    # 检查角色是否在当前场景中
                    characters_present = ""
                    char_match = re.search(r'"characters_present":\s*"([^"]*)"', current_scene)
                    if char_match:
                        characters_present = char_match.group(1).lower()
                    
                    # 添加相关的角色信息
                    for char_info in selected_characters:
                        name_match = re.search(r'Character name:[^:]*?:\s*(\w+)', char_info)
                        if name_match:
                            char_name = name_match.group(1)
                            if char_name.lower() in characters_present:
                                char_content_match = re.search(r'##[^{]*:\{(.*?)\}', char_info, re.DOTALL)
                                if char_content_match:
                                    scene_content += char_content_match.group(1).strip() + "\n\n"
                                else:
                                    scene_content += char_info + "\n\n"
                    
                    # 添加场景内容并去除前导空格
                    scene_content += current_scene.strip()
                    scene_text = remove_leading_spaces(scene_content)
                    break
            
            # 处理故事内容
            for match in story_matches:
                if extract_index(match) == current_index:
                    story_index = match.group(1)
                    story_content = json.loads("{" + match.group(2) + "}")
                    story_text_cn = story_content.get("narrative_cn", "")
                    story_text_en = story_content.get("narrative_en", "")
                    break
            
            # 添加前置文本
            if appstart_text:
                if '##' in appstart_text:
                    appstart_matches = re.finditer(r'##[^{]*:\{(.*?)\}', appstart_text, re.DOTALL)
                    appstart_text = '\n\n'.join(m.group(1).strip() for m in appstart_matches)
                scene_text = f"{appstart_text}\n{scene_text}"
            
            # 添加后置文本
            if append_text:
                if '##' in append_text:
                    append_matches = re.finditer(r'##[^{]*:\{(.*?)\}', append_text, re.DOTALL)
                    append_text = '\n\n'.join(m.group(1).strip() for m in append_matches)
                scene_text = f"{scene_text}\n{append_text}"
            
            # 添加前缀和后缀
            scene_text = f"{prefix}{scene_text}{suffix}"
            
            # 计算下一个索引
            next_index = current_index + 1
            if next_index > max_index:
                next_index = 1
            
            # 更新索引
            if unique_id:
                text_indices[unique_id] = next_index
                self._update_index(unique_id, next_index)
                print(f"[TextProcessor] 更新索引: {current_index} -> {next_index}")
            
            return (story_name, story_cover, story_summary, scene_index, scene_text, 
                   story_index, story_text_cn, story_text_en, character_name, character_text, 
                   current_index, max_index)
            
        except Exception as e:
            print(f"[TextProcessor] 处理文本时出错: {str(e)}")
            return "", "", "", "", "", "", "", "", character_name, "", text_index, 1

    def _update_index(self, node_id: str, index: int):
        """更新节点索引"""
        try:
            if node_id:
                PromptServer.instance.send_sync("impact-node-feedback", {
                    "node_id": node_id,
                    "widget_name": "text_index",
                    "type": "int",
                    "value": index
                })
                print(f"[TextProcessor] 更新索引成功: {index}")
        except Exception as e:
            print(f"[TextProcessor] 更新索引失败: {str(e)}") 
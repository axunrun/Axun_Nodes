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

def load_shot_presets():
    """加载镜头预设"""
    try:
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取配置文件路径
        config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config", "AIAssistant_presets.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            presets = json.load(f)
            return list(presets.get("shot_presets", {}).keys())
    except Exception as e:
        print(f"[TextProcessor] 加载镜头预设失败: {str(e)}")
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

# 添加路由用于获取最新的镜头预设列表
@PromptServer.instance.routes.get("/axun-text/shot-presets")
async def get_shot_presets(request):
    """获取最新的镜头预设列表"""
    try:
        presets = load_shot_presets()
        return web.json_response({"presets": presets})
    except Exception as e:
        print(f"[TextProcessor] 获取镜头预设列表失败: {str(e)}")
        return web.json_response({"presets": ["null"]})

class TextProcessor:
    """文本处理器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        character_presets = load_character_presets()
        shot_presets = load_shot_presets()
        return {
            "required": {
                "character_a_preset": (character_presets,),
                "character_b_preset": (character_presets,),
                "character_c_preset": (character_presets,),
                "shot_preset": (shot_presets,),
                "appstart_text": ("STRING", {"multiline": True, "default": ""}),
                "append_text": ("STRING", {"multiline": True, "default": ""}),
                "content_type": ("STRING", {"default": "scene_*,story_*", "multiline": False}),
                "scene_index": ("INT", {"default": 1, "min": 1, "max": 999999}),
            },
            "optional": {
                "sample_character": ("STRING", {"multiline": True}),
                "sample_story": ("STRING", {"multiline": True}),
                "sample_cover": ("STRING", {"multiline": True}),
                "sample_animation": ("STRING", {"multiline": True}),
                "sample_reasoning": ("STRING", {"multiline": True}),
                "sample_enter": ("STRING", {"multiline": True}),
                "sample_all_story": ("STRING", {"multiline": True}),
                "in_path": ("STRING", {"default": ""}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ('character_prompt', 'scene_prompt', 'cover_prompt', 'animation_prompt', 'reasoning_prompt', 'enter_prompt', 
                   'current_index', 'max_scene', 'save_text', 'file_name', 'out_path')
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

    def get_shot_prompt(self, preset_name):
        """获取镜头预设信息"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config", "AIAssistant_presets.json")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                presets = json.load(f)
                shot_info = presets.get("shot_presets", {}).get(preset_name, {})
                if shot_info and preset_name != "null":
                    return shot_info.get("prompt", "")
        except Exception as e:
            print(f"[TextProcessor] 获取镜头信息失败: {str(e)}")
        return ""

    def extract_character_name(self, text: str) -> str:
        """提取角色名称"""
        try:
            print(f"[TextProcessor] 开始提取角色名称，输入文本:\n{text[:200]}...")
            
            # 使用正则表达式匹配 "Character name:" 后面的内容
            match = re.search(r'Character name:\s*\n\s*([^:\n]+):\s*([^:\n]+)', text, re.IGNORECASE | re.MULTILINE)
            if match:
                role = match.group(1).strip()
                char_name = match.group(2).strip()
                print(f"[TextProcessor] 提取到角色类型: {role}, 名字: {char_name}")
                
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
            
            story_info_pattern = r'##story_info:\s*\{(.*?)\}\s*(?=##|$)'
            story_info_match = re.search(story_info_pattern, text, re.DOTALL)
            
            if story_info_match:
                story_info_text = story_info_match.group(1).strip()
                print(f"[TextProcessor] 找到故事信息块，长度: {len(story_info_text)}")
                
                json_str = "{" + story_info_text + "}"
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                json_str = re.sub(r'[\n\r]+\s*', ' ', json_str)
                
                try:
                    story_info = json.loads(json_str)
                    print(f"[TextProcessor] 成功解析故事信息")
                    print(f"[TextProcessor] 标题: {story_info.get('title_en', '')} / {story_info.get('title_cn', '')}")
                    
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
            
            full_text = []
            
            # 提取Character name部分
            name_match = re.search(r'Character name:\s*\n([^#]*?)(?=\n\s*Character prompts:|$)', text, re.DOTALL)
            if name_match:
                name_text = name_match.group(1).strip()
                full_text.extend(["Character name:", name_text])
            
            # 提取Character prompts部分，修改正则表达式避免捕获结尾的大括号
            prompts_match = re.search(r'Character prompts:\s*\n(.*?)(?=\n\s*\}|$)', text, re.DOTALL)
            if prompts_match:
                prompts_text = prompts_match.group(1).strip()
                if full_text:
                    full_text.append("")
                full_text.extend(["Character prompts:", prompts_text])
            
            if full_text:
                character_text = "\n".join(full_text)
                # 确保移除所有可能的结尾大括号和多余空白
                character_text = character_text.strip().rstrip('}').strip()
                print(f"[TextProcessor] 成功提取角色描述，长度: {len(character_text)}")
                return character_text
            
            print("[TextProcessor] 未找到角色描述")
            return ""
        except Exception as e:
            print(f"[TextProcessor] 提取角色描述失败: {str(e)}")
            return ""

    def append_text_content(self, main_text: str, shot_text: str = "", prefix_text: str = "", suffix_text: str = "") -> str:
        """通用的文本拼接方法"""
        result_parts = []
        
        if shot_text:
            result_parts.append(shot_text)
        
        if prefix_text:
            if '##' in prefix_text:
                prefix_matches = re.finditer(r'##[^{]*:\{(.*?)\}', prefix_text, re.DOTALL)
                prefix_text = '\n\n'.join(m.group(1).strip() for m in prefix_matches)
            result_parts.append(prefix_text)
        
        result_parts.append(main_text)
        
        if suffix_text:
            if '##' in suffix_text:
                suffix_matches = re.finditer(r'##[^{]*:\{(.*?)\}', suffix_text, re.DOTALL)
                suffix_text = '\n\n'.join(m.group(1).strip() for m in suffix_matches)
            result_parts.append(suffix_text)
        
        return '\n\n'.join(part.strip() for part in result_parts if part.strip())

    def process_text(self, character_a_preset: str, character_b_preset: str, 
                    character_c_preset: str, shot_preset: str, appstart_text: str, 
                    append_text: str, content_type: str, scene_index: int,
                    sample_character: str = "", sample_story: str = "", sample_cover: str = "", 
                    sample_animation: str = "", sample_reasoning: str = "", sample_enter: str = "", 
                    sample_all_story: str = "", in_path: str = "",
                    unique_id=None, extra_pnginfo=None):
        """处理文本内容"""
        try:
            print(f"[TextProcessor] 开始处理文本，当前索引: {scene_index}")
            
            # 获取镜头预设文本
            shot_text = self.get_shot_prompt(shot_preset) if shot_preset != "null" else ""
            
            # 初始化返回值
            character_prompt = ""
            scene_prompt = ""
            cover_prompt = ""
            animation_prompt = ""
            reasoning_prompt = sample_reasoning.strip() if sample_reasoning else ""
            enter_prompt = sample_enter.strip() if sample_enter else ""
            current_index = scene_index
            max_scene = 1
            out_path = in_path
            file_name = ""
            save_text = ""
            
            # 处理路径输出和文件名，按优先级处理输入
            if sample_character and sample_character.strip():
                # 处理角色输入
                out_path = os.path.join(in_path, "Characters") if in_path else "Characters"
                character_name = self.extract_character_name(sample_character)
                # 提取角色文本并确保不包含多余的大括号
                character_text = self.extract_character_text(sample_character)
                character_prompt = self.append_text_content(character_text, shot_text, appstart_text, append_text).rstrip('}')
                file_name = character_name
                save_text = sample_character.strip()  # 直接使用原始输入
                print(f"[TextProcessor] 处理角色输入: {character_name}")
                
            elif sample_cover and sample_cover.strip():
                # 处理封面输入
                out_path = os.path.join(in_path, "Cover") if in_path else "Cover"
                story_info = self.extract_story_info(sample_cover)
                if story_info:
                    title_en = story_info.get("title_en", "")
                    title_cn = story_info.get("title_cn", "")
                    if title_en and title_cn:
                        story_name = f"{title_en.replace(' ', '_')}_{title_cn}"
                        file_name = f"{story_name}_cover"
                    cover_prompt_data = story_info.get("cover_prompt", {})
                    if cover_prompt_data:
                        cover_json = json.dumps(cover_prompt_data, ensure_ascii=False, indent=2)
                        cover_prompt_original = self.remove_leading_spaces(cover_json[1:-1].strip())
                        cover_prompt = self.append_text_content(cover_prompt_original, shot_text, appstart_text, append_text)
                        
                    summary_en = story_info.get("summary_en", "")
                    summary_cn = story_info.get("summary_cn", "")
                    if summary_en and summary_cn:
                        summary_dict = {
                            "summary_en": summary_en,
                            "summary_cn": summary_cn
                        }
                        summary_json = json.dumps(summary_dict, ensure_ascii=False, indent=2)
                        story_summary = self.remove_leading_spaces(summary_json[1:-1].strip())
                        save_text = f"{cover_prompt_original}\n\n{story_summary}"
                    else:
                        save_text = cover_prompt_original

            elif sample_animation and sample_animation.strip():
                # 处理动画输入
                out_path = os.path.join(in_path, "Animation") if in_path else "Animation"
                file_name = "animation"
                # 设置 animation_prompt 和 save_text
                animation_prompt = sample_animation.strip()
                save_text = sample_animation.strip()
                        
            elif sample_reasoning and sample_reasoning.strip():
                # 处理推理输入
                out_path = os.path.join(in_path, "Other") if in_path else "Other"
                file_name = "Image_reasoning"
                reasoning_prompt = self.append_text_content(sample_reasoning.strip(), shot_text, appstart_text, append_text)
                save_text = sample_reasoning.strip()
                
            elif sample_enter and sample_enter.strip():
                # 处理手动输入
                out_path = os.path.join(in_path, "Other") if in_path else "Other"
                file_name = "Manual_entry"
                enter_prompt = self.append_text_content(sample_enter.strip(), shot_text, appstart_text, append_text)
                save_text = sample_enter.strip()

            elif sample_all_story and sample_all_story.strip():
                # 处理全故事输入
                out_path = os.path.join(in_path, "Allstory") if in_path else "Allstory"
                save_text = sample_all_story.strip()
                
                # 从文本中提取 title_cn
                try:
                    print("[TextProcessor] 开始解析story_info")
                    # 使用正则表达式直接提取 title_cn
                    title_match = re.search(r'"title_cn":\s*"([^"]+)"', sample_all_story)
                    if title_match:
                        title_cn = title_match.group(1)
                        print(f"[TextProcessor] 成功提取标题: {title_cn}")
                        file_name = title_cn
                    else:
                        print("[TextProcessor] 未找到title_cn字段")
                        file_name = "all_story"
                except Exception as e:
                    print(f"[TextProcessor] 提取标题失败: {str(e)}")
                    print("[TextProcessor] 错误详情:")
                    traceback.print_exc()
                    file_name = "all_story"
                
            elif sample_story and sample_story.strip():
                # 处理故事输入
                out_path = os.path.join(in_path, "Story") if in_path else "Story"
                out_path = out_path.replace("\\", "/")
                
                story_info = self.extract_story_info(sample_story)
                story_name = ""
                if story_info:
                    title_en = story_info.get("title_en", "")
                    title_cn = story_info.get("title_cn", "")
                    if title_en and title_cn:
                        story_name = f"{title_en.replace(' ', '_')}_{title_cn}"
                        print(f"[TextProcessor] 生成故事名称: {story_name}")
                
                selected_characters = []
                for preset_name in [character_a_preset, character_b_preset, character_c_preset]:
                    if preset_name != "null":
                        char_info = self.get_character_info(preset_name)
                        if char_info:
                            selected_characters.append(char_info)
                            print(f"[TextProcessor] 添加角色: {preset_name}")
                
                content_types = [t.strip() for t in content_type.split(',')]
                
                patterns = []
                for ct in content_types:
                    if '*' in ct:
                        pattern = ct.replace('*', r'\d+')
                    else:
                        pattern = ct
                    patterns.append(f"##({pattern}):\s*\{{(.*?)\}}")
                
                all_matches = []
                for pattern in patterns:
                    matches = list(re.finditer(pattern, sample_story, re.DOTALL))
                    all_matches.extend(matches)
                
                if not all_matches:
                    return (character_prompt, scene_prompt, cover_prompt, animation_prompt, reasoning_prompt, enter_prompt,
                           current_index, max_scene, save_text, file_name, out_path)
                
                scene_matches = []
                story_matches = []
                for match in all_matches:
                    full_match = match.group(1)
                    if 'scene_' in full_match:
                        scene_matches.append(match)
                    elif 'story_' in full_match:
                        story_matches.append(match)
                
                if not scene_matches:
                    return (character_prompt, scene_prompt, cover_prompt, animation_prompt, reasoning_prompt, enter_prompt,
                           current_index, max_scene, save_text, file_name, out_path)
                
                def extract_index(match):
                    try:
                        full_match = match.group(1)
                        return int(full_match.split('_')[1])
                    except Exception as e:
                        print(f"[TextProcessor] 提取索引出错: {str(e)}")
                        return 0
                
                max_scene = max(extract_index(m) for m in scene_matches)
                current_index = ((scene_index - 1) % max_scene) + 1
                
                for match in scene_matches:
                    if extract_index(match) == current_index:
                        scene_index = match.group(1)
                        current_scene = match.group(2)
                        
                        scene_content = ""
                        
                        # 1. 提取characters_present
                        char_match = re.search(r'"characters_present":\s*\[(.*?)\]', current_scene)
                        if char_match:
                            chars_text = "[" + char_match.group(1) + "]"
                            try:
                                characters_present = json.loads(chars_text)
                                characters_present = [name.lower() for name in characters_present]
                                print(f"[TextProcessor] 场景中的角色: {characters_present}")
                                # 保留characters_present部分
                                scene_content += f'"characters_present": {chars_text}\n'
                            except json.JSONDecodeError:
                                print("[TextProcessor] 解析characters_present失败")
                        
                        # 2. 提取scene_description部分
                        scene_desc = re.search(r'"scene_description":\s*(.*?)(?=\}|$)', current_scene, re.DOTALL)
                        if scene_desc:
                            scene_content += f'"scene_description":\n{scene_desc.group(1).strip()}\n'
                        
                        # 3. 处理角色内容
                        character_contents = []
                        for char_info in selected_characters:
                            # 提取角色名称
                            name_match = re.search(r'Character name:\s*\n[^:]*:\s*(\w+)', char_info, re.DOTALL)
                            if name_match:
                                char_name = name_match.group(1).strip()
                                print(f"[TextProcessor] 检查角色: {char_name}")
                                if char_name.lower() in characters_present:
                                    print(f"[TextProcessor] 添加角色内容: {char_name}")
                                    # 提取大括号内的内容
                                    char_content_match = re.search(r'\{(.*?)\}', char_info, re.DOTALL)
                                    if char_content_match:
                                        # 提取并清理内容
                                        content = char_content_match.group(1).strip()
                                        character_contents.append(content)
                            else:
                                print(f"[TextProcessor] 未能提取角色名称: {char_info[:100]}...")
                        
                        # 4. 将角色内容添加到场景内容后面
                        if character_contents:
                            scene_content += "\n\n" + "\n\n".join(character_contents)
                        
                        scene_content = self.remove_leading_spaces(scene_content)
                        scene_prompt = self.append_text_content(scene_content, shot_text, appstart_text, append_text)
                        break
                
                for match in story_matches:
                    if extract_index(match) == current_index:
                        story_index = match.group(1)
                        story_text = match.group(2).strip()
                        
                        # 修改正则表达式以匹配完整的引号内容
                        cn_match = re.search(r'"narrative_cn":\s*"(.*?)"(?=\s*[,}])', story_text, re.DOTALL)
                        en_match = re.search(r'"narrative_en":\s*"(.*?)"(?=\s*[,}])', story_text, re.DOTALL)
                        
                        if cn_match and en_match:
                            story_text_cn = cn_match.group(1).strip()
                            story_text_en = en_match.group(1).strip()
                            save_text = f"{story_text_cn}\n\n{story_text_en}"
                            print(f"[TextProcessor] 提取故事内容 CN: {story_text_cn[:50]}...")
                            print(f"[TextProcessor] 提取故事内容 EN: {story_text_en[:50]}...")
                        else:
                            print("[TextProcessor] 未能完整提取故事内容")
                            save_text = ""
                        break
                
                if story_name and story_index:
                    file_name = f"{story_name}_{story_index}"
                
                if unique_id:
                    next_index = (current_index % max_scene) + 1
                    text_indices[unique_id] = next_index
                    self._update_index(unique_id, next_index)
                    print(f"[TextProcessor] 更新索引: {current_index} -> {next_index}")
            
            # 替换路径中的反斜杠
            out_path = out_path.replace("\\", "/")
            
            return (character_prompt, scene_prompt, cover_prompt, animation_prompt, reasoning_prompt, enter_prompt,
                   current_index, max_scene, save_text, file_name, out_path)
            
        except Exception as e:
            print(f"[TextProcessor] 处理文本时出错: {str(e)}")
            traceback.print_exc()
            return "", "", "", "", "", "", scene_index, 1, "", "", out_path

    def remove_leading_spaces(self, json_str: str) -> str:
        """移除JSON字符串中每行开头的空格"""
        lines = json_str.split('\n')
        cleaned_lines = [line.lstrip() for line in lines]
        return '\n'.join(cleaned_lines)

    def _update_index(self, node_id: str, index: int):
        """更新节点索引"""
        try:
            if node_id:
                PromptServer.instance.send_sync("impact-node-feedback", {
                    "node_id": node_id,
                    "widget_name": "scene_index",
                    "type": "int",
                    "value": index
                })
                print(f"[TextProcessor] 更新索引成功: {index}")
        except Exception as e:
            print(f"[TextProcessor] 更新索引失败: {str(e)}") 
"""
Story Extractor Node for ComfyUI
提供中文故事内容提取功能
"""

import re
import json
from server import PromptServer

class StoryExtractor:
    """故事提取器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "sample_story": ("STRING", {"multiline": True, "default": ""}),
                "extracted_text": ("STRING", {
                    "multiline": True,
                    "default": "提取的内容将显示在这里...",
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "extract_story"
    CATEGORY = "!Axun Nodes/AIAssistant"
    OUTPUT_NODE = True

    def extract_story(self, sample_story: str, extracted_text: str, unique_id: str) -> tuple:
        """提取故事内容"""
        try:
            result = []
            print("[StoryExtractor] 开始处理故事内容...")
            
            # 提取故事信息
            print("[StoryExtractor] 尝试匹配story_info...")
            story_info_pattern = r'##story_info:\s*({(?:[^{}]|{[^{}]*})*})'
            story_info_match = re.search(story_info_pattern, sample_story, re.DOTALL)
            
            if story_info_match:
                try:
                    # 清理和格式化 JSON 字符串
                    json_str = story_info_match.group(1).strip()
                    print(f"[StoryExtractor] 找到story_info: {json_str[:100]}...")
                    story_info = json.loads(json_str)
                    
                    # 提取标题和简介
                    title = story_info.get('title_cn', '')
                    summary = story_info.get('summary_cn', '')
                    
                    if title:
                        result.append(f"故事名称：{title}")
                        print(f"[StoryExtractor] 提取到标题: {title}")
                    if summary:
                        result.append(f"故事简介：{summary}")
                        print(f"[StoryExtractor] 提取到简介: {summary[:100]}...")
                        
                except json.JSONDecodeError as e:
                    print(f"[StoryExtractor] 解析story_info失败: {str(e)}")
                    print(f"[StoryExtractor] 尝试解析的JSON: {json_str}")
            else:
                print("[StoryExtractor] 未找到story_info部分")
            
            # 提取所有故事章节
            print("[StoryExtractor] 开始提取故事章节...")
            story_pattern = r'##story_(\d+):\s*({(?:[^{}]|{[^{}]*})*})'
            story_matches = re.finditer(story_pattern, sample_story, re.DOTALL)
            chapters = []
            
            for match in story_matches:
                chapter_num = int(match.group(1))
                try:
                    # 清理和格式化 JSON 字符串
                    json_str = match.group(2).strip()
                    print(f"[StoryExtractor] 找到第{chapter_num}章: {json_str[:100]}...")
                    chapter_content = json.loads(json_str)
                    narrative = chapter_content.get('narrative_cn', '')
                    if narrative:
                        chapters.append((chapter_num, narrative))
                        print(f"[StoryExtractor] 成功提取第{chapter_num}章内容")
                except json.JSONDecodeError as e:
                    print(f"[StoryExtractor] 解析story_{chapter_num}失败: {str(e)}")
                    print(f"[StoryExtractor] 尝试解析的JSON: {json_str}")
            
            # 按章节号排序
            chapters.sort(key=lambda x: x[0])
            print(f"[StoryExtractor] 总共提取到{len(chapters)}个章节")
            
            # 添加章节内容
            for num, content in chapters:
                result.append(f"\n第{num}章：\n{content}")
            
            # 如果没有找到任何内容
            if not result:
                print("[StoryExtractor] 未能提取到任何内容")
                final_text = "未能提取到任何故事内容。"
            else:
                # 合并所有内容
                final_text = "\n".join(result)
                print(f"[StoryExtractor] 成功提取内容，总长度：{len(final_text)}")

            # 发送结果到前端显示
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": unique_id,
                    "widget_name": "extracted_text",
                    "type": "text",
                    "value": final_text
                }
            )
            
            return ()
            
        except Exception as e:
            error_msg = f"处理故事内容时发生错误：{str(e)}"
            print(f"[StoryExtractor] {error_msg}")
            # 发送错误信息到前端显示
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": unique_id,
                    "widget_name": "extracted_text",
                    "type": "text",
                    "value": error_msg
                }
            )
            return ()

    @classmethod
    def VALIDATE_INPUTS(cls, sample_story: str, extracted_text: str = "", unique_id: str = ""):
        """验证输入"""
        return True 
import re
from server import PromptServer
from aiohttp import web
import json

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

class TextProcessor:
    """文本处理器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "appstart_text": ("STRING", {"multiline": True, "default": ""}),
                "sample_text": ("STRING", {"multiline": True}),
                "append_text": ("STRING", {"multiline": True, "default": ""}),
                "content_type": ("STRING", {"default": "page_*_image_en", "multiline": False}),
                "prefix": ("STRING", {"default": ""}),
                "suffix": ("STRING", {"default": ""}),
                "text_index": ("INT", {"default": 1, "min": 1, "max": 999999}),
            },
            "hidden": {
                "id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("combined_text", "current_index")
    FUNCTION = "process_text"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def process_text(self, appstart_text: str, sample_text: str, append_text: str, content_type: str, prefix: str, suffix: str, text_index: int, id: str):
        """处理文本内容"""
        # 分割多个内容类型
        content_types = [ct.strip() for ct in content_type.split(',')]
        texts_by_type = {}  # 按类型存储文本
        page_numbers = set()  # 存储所有页面编号
        
        # 处理每个内容类型
        for ct in content_types:
            texts_by_type[ct] = []
            try:
                # 提取指定格式的内容
                # 支持多种格式：page_数字_任意文本
                pattern = f'"{ct.replace("*", "(\\d+)")}":\\s*"([^"]*)"'
                matches = list(re.finditer(pattern, sample_text))
                
                if not matches:
                    print(f"警告: 未找到匹配的内容类型 '{ct}'")
                    continue
                
                # 收集当前类型的所有匹配文本，并记录页面编号
                for match in matches:
                    try:
                        page_num = int(match.group(1))  # 获取页面编号
                        text = match.group(2).strip()   # 获取文本内容
                        if text:  # 确保文本不为空
                            texts_by_type[ct].append((page_num, text))
                            page_numbers.add(page_num)
                    except (IndexError, ValueError) as e:
                        print(f"处理文本时出错 '{ct}': {str(e)}")
                        continue
                    
            except Exception as e:
                print(f"处理内容类型 '{ct}' 时出错: {str(e)}")
                continue
        
        # 如果没有找到任何匹配的文本
        if not page_numbers:
            text_indices[id] = 1
            self._update_index(id, 1)
            return "", 1
        
        # 将页面编号排序
        sorted_pages = sorted(list(page_numbers))
        
        # 获取当前索引，优先使用手动设置的值
        current_index = text_index if text_index is not None else text_indices.get(id, 1)
        
        # 确保索引在有效范围内
        max_index = len(sorted_pages)
        current_index = ((current_index - 1) % max_index) + 1
        
        # 获取当前页面编号
        current_page = sorted_pages[current_index - 1]
        
        # 组合当前页面的所有类型文本
        result_texts = []
        for ct in content_types:
            # 从当前类型的文本中找到对应页面的文本
            matching_texts = [text for page, text in texts_by_type[ct] if page == current_page]
            if matching_texts:
                result_texts.append(matching_texts[0])
            else:
                print(f"警告: 页面 {current_page} 未找到内容类型 '{ct}' 的文本")
        
        # 用换行符连接多个文本
        combined_text = "\n".join(result_texts)
        
        # 添加前缀和后缀
        wrapped_text = f"{prefix}{combined_text}{suffix}"
        
        # 添加前置文本（如果有）
        if appstart_text:
            wrapped_text = f"{appstart_text}\n{wrapped_text}"
            
        # 添加后置文本（如果有）
        if append_text:
            wrapped_text = f"{wrapped_text}\n{append_text}"
            
        # 计算并保存下一个索引
        next_index = current_index + 1
        if next_index > max_index:
            next_index = 1
        text_indices[id] = next_index
        self._update_index(id, next_index)
            
        return wrapped_text, current_index

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
            print(f"更新索引失败: {str(e)}") 
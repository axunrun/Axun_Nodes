import copy
from typing import Dict, Any, List

class TextMerger:
    """文本合并节点：将多个输入文本以段落方式合并"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """定义节点输入类型"""
        return {
            "optional": {
                "text1": ("STRING", {"multiline": True}),
                "text2": ("STRING", {"multiline": True}),
                "text3": ("STRING", {"multiline": True}),
                "text4": ("STRING", {"multiline": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "merge_texts"
    CATEGORY = "!Axun Nodes/AIAssistant"
    
    RETURN_NAMES = ("merged_text",)
    
    def merge_texts(self, **kwargs) -> tuple[str]:
        """合并文本的主要逻辑"""
        # 过滤掉None值（未连接或被忽略的输入）
        valid_texts = [text for text in kwargs.values() if text is not None]
        
        # 使用两个换行符合并文本
        merged = "\n\n".join(valid_texts)
        
        return (merged,) 
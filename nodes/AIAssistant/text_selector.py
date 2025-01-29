import copy
from typing import Dict, Any, List

class TextSelector:
    """文本选择器节点：按优先级选择输入文本"""
    
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
    FUNCTION = "select_text"
    CATEGORY = "!Axun Nodes/AIAssistant"
    
    RETURN_NAMES = ("selected_text",)
    
    def select_text(self, **kwargs) -> tuple[str]:
        """按优先级选择文本的主要逻辑"""
        try:
            print("[TextSelector] 开始处理文本")
            
            # 按优先级顺序检查文本
            for i in range(1, 5):
                text_key = f"text{i}"
                if text_key in kwargs and kwargs[text_key] is not None and kwargs[text_key].strip():
                    selected_text = kwargs[text_key].strip()
                    print(f"[TextSelector] 选择了text{i}作为输出")
                    return (selected_text,)
            
            # 如果所有输入都为空，返回空字符串
            print("[TextSelector] 所有输入为空，返回空字符串")
            return ("",)
            
        except Exception as e:
            print(f"[TextSelector] 处理文本时出错: {str(e)}")
            return ("",) 
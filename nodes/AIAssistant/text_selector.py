import copy
from typing import Dict, Any, List

class TextSelector:
    """文本选择器节点：按优先级选择输入文本"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """定义节点输入类型"""
        return {
            "optional": {
                "text1": ("STRING", {"multiline": True}),  # 最高优先级文本
                "text2": ("STRING", {"multiline": True}),  # 第二优先级文本
                "text3": ("STRING", {"multiline": True}),  # 第三优先级文本
                "text4": ("STRING", {"multiline": True}),  # 第四优先级文本
                "text5": ("STRING", {"multiline": True}),  # 第五优先级文本
                "text6": ("STRING", {"multiline": True}),  # 第六优先级文本
                "text7": ("STRING", {"multiline": True}),  # 第七优先级文本
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "select_text"
    CATEGORY = "!Axun Nodes/AIAssistant"
    
    RETURN_NAMES = ("selected_text",)
    
    def select_text(self, **kwargs) -> tuple[str]:
        """按优先级选择文本的主要逻辑
        优先级：text1 > text2 > text3 > text4 > text5 > text6 > text7
        如果高优先级文本为空，则尝试使用下一优先级的文本
        所有文本都为空时返回空字符串
        """
        try:
            print("[TextSelector] 开始处理文本")
            
            # 按优先级顺序检查文本
            for i in range(1, 8):  # 修改为1-7
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
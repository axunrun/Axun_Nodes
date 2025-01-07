from typing import Tuple, Dict, Any
import logging

# 配置日志
logger = logging.getLogger("axun_nodes.work_mode")

class WorkMode:
    """
    工作模式节点
    用于控制批量处理或单次处理模式
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": ("BOOLEAN", {
                    "default": True,
                    "label_on": "批量模式",
                    "label_off": "单次模式"
                }),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("mode",)
    FUNCTION = "process"
    CATEGORY = "!Axun Nodes/Queue Tools"

    def switch_mode(self, mode):
        return (mode,) 
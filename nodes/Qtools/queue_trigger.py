from typing import Tuple, Dict, Any
import logging
import time
from server import PromptServer

# 配置日志
logger = logging.getLogger("axun_nodes.queue_trigger")

# 定义任意类型
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any_typ = AnyType("*")

class ImpactQueueTriggerCountdown:
    """
    队列触发计数器节点
    功能：
    1. 批量任务队列触发
    2. 计数管理
    3. 延迟控制
    4. 断点续传
    5. 任意类型信号传递
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "count": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                }),
                "total": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                }),
                "queue_mode": ("BOOLEAN", {
                    "default": True,
                    "label_on": "批量模式",
                    "label_off": "单次模式"
                }),
                "delay_ms": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 100,
                }),
                "start_image": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                }),
            },
            "optional": {
                "any_in": (any_typ,),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = (any_typ, "INT", "INT")
    RETURN_NAMES = ("any_out", "count", "total")
    FUNCTION = "trigger_queue"
    CATEGORY = "!Axun Nodes/Queue Tools"
    OUTPUT_NODE = True

    def __init__(self):
        self._initialized = False
        self._last_count = 0

    def trigger_queue(
        self,
        count: int,
        total: int,
        queue_mode: bool,
        delay_ms: int,
        start_image: int,
        unique_id: str,
        any_in: Any = None
    ) -> Tuple[Any, int, int]:
        try:
            # 处理延迟
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
                
            # 初始化计数
            if not self._initialized:
                count = start_image
                self._initialized = True
                self._update_count(unique_id, count)
                
            # 计算剩余任务数
            remaining_tasks = total - start_image
                
            # 批量模式下处理队列
            if queue_mode:
                if count < remaining_tasks - 1:
                    # 递增计数
                    next_count = count + 1
                    self._update_count(unique_id, next_count)
                    self._add_to_queue()
                    count = next_count
                    self._last_count = count
                elif count >= remaining_tasks - 1:
                    self._update_count(unique_id, 0)
                    count = 0
                    self._last_count = 0

            return (any_in, count, total)
            
        except Exception as e:
            logger.error(f"队列触发失败: {str(e)}")
            return (any_in, self._last_count, total)

    def _update_count(self, node_id: str, count: int):
        """更新计数器"""
        try:
            PromptServer.instance.send_sync(
                "impact-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "count",
                    "type": "int",
                    "value": count
                }
            )
        except Exception as e:
            logger.error(f"更新计数失败: {str(e)}")

    def _add_to_queue(self):
        """添加任务到队列"""
        try:
            PromptServer.instance.send_sync("impact-add-queue", {})
        except Exception as e:
            logger.error(f"添加队列失败: {str(e)}") 
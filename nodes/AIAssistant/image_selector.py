import torch

class ImageSelector:
    """图像选择器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": ("IMAGE",),
                "image_b": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "select_image"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def select_image(self, image_a: torch.Tensor, image_b: torch.Tensor):
        """选择输出图像
        如果image_a有输入，则输出image_a
        否则输出image_b
        """
        try:
            # 检查image_a是否为空
            if image_a is not None and image_a.numel() > 0:
                print("[ImageSelector] 使用第一张图像")
                return (image_a,)
            else:
                print("[ImageSelector] 使用第二张图像")
                return (image_b,)
        except Exception as e:
            print(f"[ImageSelector] 处理图像时出错: {str(e)}")
            # 如果出错，返回image_b
            return (image_b,)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageSelector": ImageSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSelector": "Image Selector 图像选择器"
} 
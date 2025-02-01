import torch

class ImageSelector:
    """图像选择器节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},  # 没有必需输入
            "optional": {
                "image_a": ("IMAGE",),  # 第一优先级图像
                "image_b": ("IMAGE",),  # 第二优先级图像
                "image_c": ("IMAGE",),  # 第三优先级图像
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "select_image"
    CATEGORY = "!Axun Nodes/AIAssistant"

    def is_valid_image(self, image) -> bool:
        """检查图像是否有效
        Args:
            image: 输入图像（可能是张量或其他类型）
        Returns:
            bool: 图像是否有效
        """
        if image is None:
            return False
            
        try:
            # 检查是否为 torch.Tensor
            if not isinstance(image, torch.Tensor):
                return False
                
            # 检查维度和数据
            if len(image.shape) < 3:
                return False
                
            if image.numel() == 0:
                return False
                
            return True
        except:
            return False

    def select_image(self, image_a=None, image_b=None, image_c=None):
        """选择输出图像
        优先级：image_a > image_b > image_c
        如果image_a有效，则输出image_a
        否则如果image_b有效，则输出image_b
        否则如果image_c有效，则输出image_c
        如果都无效，则输出None
        
        Args:
            image_a: 第一优先级图像，可选
            image_b: 第二优先级图像，可选
            image_c: 第三优先级图像，可选
            
        Returns:
            tuple: (selected_image,) 选中的图像或None
        """
        try:
            # 按优先级检查图像
            if self.is_valid_image(image_a):
                print("[ImageSelector] 使用第一优先级图像")
                return (image_a,)
            
            if self.is_valid_image(image_b):
                print("[ImageSelector] 使用第二优先级图像")
                return (image_b,)
            
            if self.is_valid_image(image_c):
                print("[ImageSelector] 使用第三优先级图像")
                return (image_c,)
            
            # 所有输入都无效，返回None
            print("[ImageSelector] 所有输入图像无效，返回None")
            return (None,)
            
        except Exception as e:
            print(f"[ImageSelector] 处理图像时出错: {str(e)}")
            # 发生错误时返回None
            return (None,)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageSelector": ImageSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSelector": "🔄 Image Selector 图像选择器"
} 
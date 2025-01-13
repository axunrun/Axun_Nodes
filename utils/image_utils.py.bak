import base64
import io
from PIL import Image
import torch
import numpy as np
import logging

logger = logging.getLogger('axun.image')

def encode_image(image_tensor: torch.Tensor) -> str:
    """
    将图像张量编码为base64字符串
    Args:
        image_tensor: [B, H, W, C] 格式的图像张量
    Returns:
        base64编码的图像字符串
    """
    try:
        # 类型检查
        if not isinstance(image_tensor, torch.Tensor):
            raise TypeError(f"Expected torch.Tensor, got {type(image_tensor)}")
            
        # 维度检查
        if len(image_tensor.shape) != 4:
            raise ValueError(f"Expected 4D tensor [B,H,W,C], got shape {image_tensor.shape}")
            
        # 只处理第一张图片
        image = image_tensor[0]
        
        # 确保值范围在[0,1]之间
        if image.min() < 0 or image.max() > 1:
            logger.warning("Image values outside [0,1] range, clipping...")
            image = torch.clamp(image, 0, 1)
        
        # 转换为PIL图像
        image_np = (image * 255).byte().cpu().numpy()
        if image_np.shape[2] == 3:  # RGB
            pil_image = Image.fromarray(image_np, 'RGB')
        elif image_np.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(image_np, 'RGBA')
        else:
            raise ValueError(f"Unsupported number of channels: {image_np.shape[2]}")
        
        # 转换为JPEG格式的base64字符串
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=95)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
        
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        return "" 
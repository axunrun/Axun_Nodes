import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json

logger = logging.getLogger('axun.image')

def encode_comfy_image(image_tensor: torch.Tensor, image_format: str = "WEBP", lossless: bool = True) -> str:
    """
    将图像张量编码为base64字符串
    Args:
        image_tensor: [B, H, W, C] 格式的图像张量
        image_format: 图像格式，默认为WEBP
        lossless: 是否无损压缩，默认为True
    Returns:
        JSON字符串，包含所有图像的base64编码
    """
    try:
        # 类型检查
        if not isinstance(image_tensor, torch.Tensor):
            raise TypeError(f"Expected torch.Tensor, got {type(image_tensor)}")
            
        # 维度检查
        if len(image_tensor.shape) != 4:
            raise ValueError(f"Expected 4D tensor [B,H,W,C], got shape {image_tensor.shape}")
        
        # 存储所有图像的base64编码
        image_dict = {}
        
        # 处理批次中的每张图片
        for i in range(image_tensor.shape[0]):
            image = image_tensor[i]
            
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
            
            # 转换为指定格式的base64字符串
            buffer = io.BytesIO()
            if image_format.upper() == "WEBP":
                pil_image.save(buffer, format="WEBP", quality=100 if lossless else 95, lossless=lossless)
            else:
                pil_image.save(buffer, format=image_format.upper(), quality=95)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            image_dict[f"image_{i}"] = image_base64
        
        return json.dumps(image_dict)
        
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        return json.dumps({}) # 返回空字典的JSON字符串 
import os
import torch
import folder_paths
import comfy.model_management as mm
from comfy.utils import load_torch_file, ProgressBar

import logging
import json
from diffusers.models import UNet2DConditionModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def get_config_path(filename):
    """获取配置文件的完整路径并验证文件存在"""
    script_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(script_directory, "config", filename)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件 {filename} 不存在于路径: {config_path}")
    return config_path

class LoadLotusModel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": (folder_paths.get_filename_list("diffusion_models"),{"tooltip":"models are loaded from 'ComfyUI/models/diffusion_models'"}),
            },
            "optional": {
                "precision": (["fp16", "fp32",],
                    {"default": "fp16"}
                ),
            }
        }

    RETURN_TYPES = ("LOTUSUNET",)
    RETURN_NAMES = ("lotus_unet", )
    FUNCTION = "loadmodel"
    CATEGORY = "!Axun Nodes/Lotus"

    def loadmodel(self, model, precision):
        try:
            dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[precision]
            mm.soft_empty_cache()

            lotus_model_path = folder_paths.get_full_path_or_raise("diffusion_models", model)
            
            lotus_sd = load_torch_file(lotus_model_path)
            in_channels = lotus_sd['conv_in.weight'].shape[1]
            
            # 获取并验证配置文件路径
            lotus_config = get_config_path("lotus_nodes.json")

            with open(lotus_config, 'r') as config_file:
               config_data = json.load(config_file)
            config_data["in_channels"] = in_channels
            
            lotus_unet = UNet2DConditionModel.from_config(config_data)
            
            lotus_unet.load_state_dict(lotus_sd)
            lotus_unet.to(dtype)

            lotus_model = {
                "model": lotus_unet,
                "dtype": dtype,
                "in_channels": in_channels,
            }

            return (lotus_model,)
        except Exception as e:
            log.error(f"加载 Lotus 模型时出错: {str(e)}")
            raise
    
class LotusSampler:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lotus_unet": ("LOTUSUNET",),
                "samples": ("LATENT",),
                "seed": ("INT", {"default": 123, "min": 0, "max": 2**32, "step": 1}),
                "per_batch": ("INT", {"default": 4, "min": 1, "max": 4096, "step": 1}),
                "keep_model_loaded": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("samples",)
    FUNCTION = "loadmodel"
    CATEGORY = "!Axun Nodes/Lotus"

    def loadmodel(self, lotus_unet, seed, samples, per_batch, keep_model_loaded):
        try:
            device = mm.get_torch_device()
            offload_device = mm.unet_offload_device()
            mm.soft_empty_cache()

            model = lotus_unet["model"]
            dtype = lotus_unet["dtype"]
            in_channels = lotus_unet["in_channels"]

            latents = samples["samples"].to(dtype)
            latents = latents * 0.18215

            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)

            if in_channels == 8:  # input for g model is 8 channels
                single_noise = torch.randn(latents.shape[1:], device=torch.device("cpu"), dtype=dtype, layout=torch.strided)
                repeated_noise = single_noise.unsqueeze(0).repeat(latents.shape[0], 1, 1, 1)
                latents = torch.cat([latents, repeated_noise], dim=1)

            timesteps = torch.tensor(999, device=device).long()

            task_emb = torch.tensor([1, 0], device=device, dtype=dtype).unsqueeze(0).repeat(1, 1)
            task_emb = torch.cat([torch.sin(task_emb), torch.cos(task_emb)], dim=-1).repeat(1, 1)

            # 获取并验证空文本嵌入文件路径
            empty_text_embed_path = get_config_path("empty_text_embed.pt")
            prompt_embeds = torch.load(empty_text_embed_path, weights_only=True).to(device).to(dtype)
            extended_prompt_embeds = prompt_embeds.repeat(latents.shape[0], 1, 1)

            model.to(device)
            pbar = ProgressBar(latents.shape[0])

            results = []
            for start_idx in range(0, latents.shape[0], per_batch):
                sub_images = model(
                    latents[start_idx:start_idx+per_batch].to(device),
                    timesteps,
                    encoder_hidden_states=extended_prompt_embeds[start_idx:start_idx+per_batch],
                    cross_attention_kwargs=None,
                    return_dict=False,
                    class_labels=task_emb,
                )[0]

                results.append(sub_images.cpu())
                batch_count = sub_images.shape[0]
                pbar.update(batch_count)

            if not keep_model_loaded:
                model.to(offload_device)
                mm.soft_empty_cache()

            results = torch.cat(results, dim=0)
            results = results / 0.18215

            return {"samples": results},
        except Exception as e:
            log.error(f"Lotus 采样过程出错: {str(e)}")
            raise 
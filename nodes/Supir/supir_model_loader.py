import os
import torch
import comfy.utils
import comfy.model_management as mm
from contextlib import nullcontext
import gc
from omegaconf import OmegaConf
import folder_paths
import open_clip
from contextlib import contextmanager
from transformers import (
    CLIPTextModel,
    CLIPTokenizer,
    CLIPTextConfig,
)

try:
    from accelerate import init_empty_weights
    from accelerate.utils import set_module_tensor_to_device
    is_accelerate_available = True
except:
    pass

script_directory = os.path.dirname(os.path.abspath(__file__))

def dummy_build_vision_tower(*args, **kwargs):
    # Monkey patch the CLIP class before you create an instance.
    return None

@contextmanager
def patch_build_vision_tower():
    original_build_vision_tower = open_clip.model._build_vision_tower
    open_clip.model._build_vision_tower = dummy_build_vision_tower

    try:
        yield
    finally:
        open_clip.model._build_vision_tower = original_build_vision_tower

def build_text_model_from_openai_state_dict(
        state_dict: dict,
        device,
        cast_dtype=torch.float16,    
    ):
   
    embed_dim = state_dict["text_projection"].shape[1]
    context_length = state_dict["positional_embedding"].shape[0]
    vocab_size = state_dict["token_embedding.weight"].shape[0]
    transformer_width = state_dict["ln_final.weight"].shape[0]
    transformer_heads = transformer_width // 64
    transformer_layers = len(set(k.split(".")[2] for k in state_dict if k.startswith(f"transformer.resblocks")))

    vision_cfg = None
    text_cfg = open_clip.CLIPTextCfg(
        context_length=context_length,
        vocab_size=vocab_size,
        width=transformer_width,
        heads=transformer_heads,
        layers=transformer_layers,
    )

    with patch_build_vision_tower():
        with (init_empty_weights() if is_accelerate_available else nullcontext()):
            model = open_clip.CLIP(
                embed_dim,
                vision_cfg=vision_cfg,
                text_cfg=text_cfg,
                quick_gelu=True,
                cast_dtype=cast_dtype,
            )
    if is_accelerate_available:
        for key in state_dict:
            set_module_tensor_to_device(model, key, device=device, value=state_dict[key])
    else:
        model.load_state_dict(state_dict, strict=False)
    model = model.eval()
    for param in model.parameters():
        param.requires_grad = False
    return model

class SUPIR_model_loader:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "model" :("MODEL",),
            "clip": ("CLIP",),
            "vae": ("VAE",),
            "supir_model": (folder_paths.get_filename_list("checkpoints"),),
            "fp8_unet": ("BOOLEAN", {"default": False}),
            "diffusion_dtype": (
                    [
                        'fp16',
                        'bf16',
                        'fp32',
                        'auto'
                    ], {
                        "default": 'auto'
                    }),
            },
            "optional": {
                "high_vram": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("SUPIRMODEL", "SUPIRVAE")
    RETURN_NAMES = ("SUPIR_model","SUPIR_VAE",)
    FUNCTION = "process"
    CATEGORY = "!Axun Nodes/Supir"
    DESCRIPTION = """
Loads the SUPIR model and merges it with the SDXL model.  

Diffusion type should be kept on auto, unless you have issues loading the model.  
fp8_unet casts the unet weights to torch.float8_e4m3fn, which saves a lot of VRAM but has slight quality impact.  
high_vram: uses Accelerate to load weights to GPU, slightly faster model loading.
"""

    def process(self, supir_model, diffusion_dtype, fp8_unet, model, clip, vae, high_vram=False):
        if high_vram:
            device = mm.get_torch_device()
        else:
            device = mm.unet_offload_device()
        print("Loading weights to: ", device)
        mm.unload_all_models()

        SUPIR_MODEL_PATH = folder_paths.get_full_path("checkpoints", supir_model)

        config_path = os.path.join(script_directory, "options/SUPIR_v0.yaml")
        clip_config_path = os.path.join(script_directory, "configs/clip_vit_config.json")
        tokenizer_path = os.path.join(script_directory, "configs/tokenizer")

        custom_config = {
            'diffusion_dtype': diffusion_dtype,
            'supir_model': supir_model,
            'fp8_unet': fp8_unet,
            'model': model,
            "clip": clip,
            "vae": vae
        }

        if diffusion_dtype == 'auto':
            try:
                if mm.should_use_fp16():
                    print("Diffusion using fp16")
                    dtype = torch.float16
                elif mm.should_use_bf16():
                    print("Diffusion using bf16")
                    dtype = torch.bfloat16
                else:
                    print("Diffusion using fp32")
                    dtype = torch.float32
            except:
                raise AttributeError("ComfyUI version too old, can't autodecet properly. Set your dtypes manually.")
        else:
            print(f"Diffusion using {diffusion_dtype}")
            from .SUPIR.util import convert_dtype
            dtype = convert_dtype(diffusion_dtype)
        
        if not hasattr(self, "model") or self.model is None or self.current_config != custom_config:
            self.current_config = custom_config
            self.model = None
            
            mm.soft_empty_cache()
            
            config = OmegaConf.load(config_path)
            if mm.XFORMERS_IS_AVAILABLE:
                print("Using XFORMERS")
                config.model.params.control_stage_config.params.spatial_transformer_attn_type = "softmax-xformers"
                config.model.params.network_config.params.spatial_transformer_attn_type = "softmax-xformers"
                config.model.params.first_stage_config.params.ddconfig.attn_type = "vanilla-xformers" 
                
            config.model.target = ".SUPIR.models.SUPIR_model_v2.SUPIRModel"
            pbar = comfy.utils.ProgressBar(5)

            from .sgm.util import instantiate_from_config
            #with (init_empty_weights() if is_accelerate_available else nullcontext()):
            self.model = instantiate_from_config(config.model).cpu()
            self.model.model.dtype = dtype
            pbar.update(1)
            try:
                print(f"Attempting to load SDXL model from node inputs")
                mm.load_model_gpu(model)
                sdxl_state_dict = model.model.state_dict_for_saving(None, vae.get_sd(), None)
                if is_accelerate_available:
                    for key in sdxl_state_dict:
                        set_module_tensor_to_device(self.model, key, device=device, dtype=dtype, value=sdxl_state_dict[key])
                else:
                    self.model.load_state_dict(sdxl_state_dict, strict=False)
                if fp8_unet:
                    self.model.model.to(torch.float8_e4m3fn)
                else:
                    self.model.model.to(dtype)
                del sdxl_state_dict
                pbar.update(1)
            except:
                raise Exception("Failed to load SDXL model")            
            gc.collect()
            mm.soft_empty_cache()
            #first clip model from SDXL checkpoint
            try:
                print("Loading first clip model from SDXL checkpoint")
                clip_l_sd = None
                clip_l_model = clip.load_model()
                mm.load_model_gpu(clip_l_model)
                clip_l_sd = clip.get_sd()
                clip_l_sd = model.model.model_config.process_clip_state_dict_for_saving(clip_l_sd)

                replace_prefix = {}
                replace_prefix["conditioner.embedders.0.transformer."] = ""
    
                clip_l_sd = comfy.utils.state_dict_prefix_replace(clip_l_sd, replace_prefix, filter_keys=True)
                clip_text_config = CLIPTextConfig.from_pretrained(clip_config_path)
                self.model.conditioner.embedders[0].tokenizer = CLIPTokenizer.from_pretrained(tokenizer_path)
                with (init_empty_weights() if is_accelerate_available else nullcontext()):
                    self.model.conditioner.embedders[0].transformer = CLIPTextModel(clip_text_config)
                if is_accelerate_available:
                    for key in clip_l_sd:
                        set_module_tensor_to_device(self.model.conditioner.embedders[0].transformer, key, device=device, dtype=dtype, value=clip_l_sd[key])
                else:
                    self.model.conditioner.embedders[0].transformer.load_state_dict(clip_l_sd, strict=False)
                self.model.conditioner.embedders[0].eval()
                for param in self.model.conditioner.embedders[0].parameters():
                    param.requires_grad = False
                self.model.conditioner.embedders[0].to(dtype)
                del clip_l_sd
                pbar.update(1)
            except:
                raise Exception("Failed to load first clip model from SDXL checkpoint")
            gc.collect()
            mm.soft_empty_cache()
            #second clip model from SDXL checkpoint
            try:
                print("Loading second clip model from SDXL checkpoint")
                clip_g_sd = None
                clip_g_model = clip.load_model()
                mm.load_model_gpu(clip_g_model)
                clip_g_sd = clip.get_sd()
                clip_g_sd = model.model.model_config.process_clip_state_dict_for_saving(clip_g_sd)

                replace_prefix2 = {}
                replace_prefix2["conditioner.embedders.1.model."] = ""
                clip_g_sd = comfy.utils.state_dict_prefix_replace(clip_g_sd, replace_prefix2, filter_keys=True)             
                clip_g = build_text_model_from_openai_state_dict(clip_g_sd, device, cast_dtype=dtype)
                self.model.conditioner.embedders[1].model = clip_g
                self.model.conditioner.embedders[1].model.to(dtype)
                del clip_g_sd
                pbar.update(1)
            except:
                raise Exception("Failed to load second clip model from SDXL checkpoint")
            
            try:
                print(f'Attempting to load SUPIR model: [{SUPIR_MODEL_PATH}]')
                from .SUPIR.util import load_state_dict
                supir_state_dict = load_state_dict(SUPIR_MODEL_PATH)
                if "Q" not in supir_model or not is_accelerate_available: #I don't know why this doesn't work with the Q model. 
                    for key in supir_state_dict:
                        set_module_tensor_to_device(self.model, key, device=device, dtype=dtype, value=supir_state_dict[key])
                else:
                    self.model.load_state_dict(supir_state_dict, strict=False)
                if fp8_unet:
                    self.model.model.to(torch.float8_e4m3fn)
                else:
                    self.model.model.to(dtype)
                del supir_state_dict
                pbar.update(1)
            except:
                raise Exception("Failed to load SUPIR model")
            mm.soft_empty_cache()

        return (self.model, self.model.first_stage_model,) 
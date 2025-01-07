import importlib.util
import sys
import logging
import os

# 配置日志
def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def install_tkinter():
    """安装tkinter"""
    try:
        importlib.import_module('tkinter')
    except ImportError:
        print("[AxunNodes] 正在尝试安装tkinter")
        try:
            import subprocess
            import platform
            system = platform.system()
            if system == 'Darwin':
                result = subprocess.run(['brew', 'install', 'python-tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Brew安装失败，请确保已安装brew (https://brew.sh/)")
            elif system == 'Linux':
                result = subprocess.run(['sudo', 'apt', '-y', 'install', 'python3-tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Apt安装失败")
            else:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'tk'], check=True)
                if result.returncode != 0:
                    raise Exception("Pip安装失败")
        except Exception as e:
            print("[AxunNodes] 无法安装tkinter，请尝试设置TCL_LIBRARY和TK_LIBRARY环境变量")
            print(e)

# 初始化
setup_logging()
install_tkinter()

# 导入节点
from .nodes.Qtools.path_processor import PathProcessor
from .nodes.Qtools.queue_trigger import ImpactQueueTriggerCountdown
from .nodes.Qtools.work_mode import WorkMode
from .nodes.Qtools.dir_picker import DirPicker, dir_api

# 导入 SUPIR 节点
from .nodes.Supir.supir_sample import SUPIR_sample
from .nodes.Supir.supir_first_stage import SUPIR_first_stage
from .nodes.Supir.supir_encode import SUPIR_encode
from .nodes.Supir.supir_decode import SUPIR_decode
from .nodes.Supir.supir_conditioner import SUPIR_conditioner
from .nodes.Supir.supir_model_loader import SUPIR_model_loader

# Web目录
WEB_DIRECTORY = "./web"

# 节点映射
NODE_CLASS_MAPPINGS = {
    "axun_nodes_PathProcessor": PathProcessor,
    "axun_nodes_QueueTrigger": ImpactQueueTriggerCountdown,
    "axun_nodes_WorkMode": WorkMode,
    "axun_nodes_DirPicker": DirPicker,
    # SUPIR 节点
    "SUPIR_sample": SUPIR_sample,
    "SUPIR_first_stage": SUPIR_first_stage,
    "SUPIR_encode": SUPIR_encode,
    "SUPIR_decode": SUPIR_decode,
    "SUPIR_conditioner": SUPIR_conditioner,
    "SUPIR_model_loader": SUPIR_model_loader
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "axun_nodes_PathProcessor": "Path Processor",
    "axun_nodes_QueueTrigger": "Queue Trigger",
    "axun_nodes_WorkMode": "Work Mode",
    "axun_nodes_DirPicker": "Directory Picker",
    # SUPIR 节点
    "SUPIR_sample": "SUPIR Sampler",
    "SUPIR_first_stage": "SUPIR First Stage (Denoiser)",
    "SUPIR_encode": "SUPIR Encode",
    "SUPIR_decode": "SUPIR Decode",
    "SUPIR_conditioner": "SUPIR Conditioner",
    "SUPIR_model_loader": "SUPIR Model Loader"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'dir_api']
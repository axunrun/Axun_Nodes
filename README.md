# Axun Nodes - ComfyUI 插件 v1.01

Axun Nodes 是一个用于ComfyUI的插件，提供路径处理、队列触发、SUPIR超分和翻译功能。

## 项目结构
```
axun_nodes/
├── nodes/               # 节点实现
│   ├── Qtools/         # 队列工具节点
│   │   ├── path_processor.py # 路径处理节点
│   │   ├── queue_trigger.py # 队列触发节点
│   │   ├── work_mode.py    # 工作模式节点
│   │   └── dir_picker.py   # 目录选择器节点
│   ├── Supir/          # SUPIR超分节点
│   │   ├── supir_sample.py      # 采样器节点
│   │   ├── supir_encode.py      # 编码器节点
│   │   ├── supir_decode.py      # 解码器节点
│   │   ├── supir_first_stage.py # 第一阶段处理节点
│   │   ├── supir_conditioner.py # 条件控制节点
│   │   └── supir_model_loader.py # 模型加载器
│   └── Translator/     # 翻译功能节点
│       └── translator_node.py # 翻译节点
├── web/                 # 前端实现
│   └── js/
│       ├── web.js       # 前端交互脚本
│       └── translator.js # 翻译功能脚本
├── config/             # 配置文件目录
│   └── translator.json  # 翻译API配置
├── __init__.py         # 插件初始化和节点注册
└── README.md           # 项目说明文档
```

## 功能

### Queue Tools 分组
- 路径处理节点 (Path Processor)
  - 批量/单文件模式切换
  - 文件过滤（扩展名/正则表达式）
  - 文件排序（名称/修改时间/创建时间）
  - 自动索引管理
  - 手动索引控制（loop_index）
    - 支持自动递增
    - 支持手动设置起始值
    - 支持批量队列处理
- 队列触发节点 (Queue Trigger)
  - 批量处理计数
  - 自动队列管理
- 模式切换节点 (Work Mode)
  - 批量/单文件模式切换
- 目录选择器 (Directory Picker)
  - 目录选择和保存

### SUPIR 分组
- 采样器节点 (SUPIR Sampler)
  - 扩散模型采样
  - 多种采样器选择
- 编码器节点 (SUPIR Encode)
  - 图像到潜空间的编码
  - 分块处理支持
- 解码器节点 (SUPIR Decode)
  - 潜空间到图像的解码
  - 分块处理支持
- 第一阶段处理节点 (SUPIR First Stage)
  - 图像预处理
  - 降噪处理
- 条件控制节点 (SUPIR Conditioner)
  - 提示词处理
  - CLIP模型支持
- 模型加载器 (SUPIR Model Loader)
  - 模型加载和管理
  - 支持高性能和低内存模式

### Translator 分组
- 翻译节点 (Translator)
  - 双击翻译功能
    - 支持任意文本输入框
    - 自动检测中英文
    - 智能互译功能
  - API集成
    - 使用百度翻译API
    - 高质量翻译结果
  - 性能优化
    - 防抖处理
    - 异步请求
    - 错误重试

## 设置项说明

### 路径处理节点 (Path Processor)
| 英文显示 | 中文含义 | 说明 |
|---------|---------|------|
| load_path | 载入路径 | 输入图像文件夹路径 |
| save_path | 保存路径 | 输出图像保存路径 |
| filter_type | 过滤类型 | 文件过滤方式：regex(正则表达式) / extension(扩展名) |
| filter_value | 过滤值 | 过滤条件：正则表达式或文件扩展名 |
| sort_by | 排序方式 | name(名称) / date_modified(修改时间) / date_created(创建时间) |
| sort_order | 排序顺序 | asc(升序) / desc(降序) / random(随机) |
| path_mode | 处理模式 | Batch Mode(批次模式) / Single Mode(单次模式) |
| loop_index | 循环索引 | 当前处理的文件索引，支持手动设置和自动递增 |

### SUPIR 节点
| 节点名称 | 主要参数 | 说明 |
|---------|---------|------|
| SUPIR Model Loader | model_path | 模型路径 |
| | device | 运行设备(cuda/cpu) |
| | memory_mode | 内存模式(high_perf/low_mem) |
| SUPIR Sampler | steps | 采样步数 |
| | cfg | 条件缩放因子 |
| | sampler_name | 采样器类型 |
| SUPIR Encode | tile_size | 分块大小 |
| | overlap | 重叠像素 |
| SUPIR Decode | tile_size | 分块大小 |
| | overlap | 重叠像素 |
| SUPIR First Stage | strength | 降噪强度 |
| SUPIR Conditioner | prompt | 提示词 |
| | clip_skip | CLIP跳过层数 |

### 翻译功能配置
| 配置项 | 说明 | 默认值 |
|-------|------|--------|
| appid | 百度翻译API的APPID | 预设值 |
| key | 百度翻译API的密钥 | 预设值 |

## 安装
1. 将本插件目录放入ComfyUI的`custom_nodes`目录
2. 安装依赖：`pip install -r requirements.txt`
   - Python 3.10+
   - PyTorch 2.0+
   - xformers (可选，用于加速)
   - transformers
   - omegaconf
   - einops
   - requests (用于翻译API)
3. 确保已安装tkinter：
   - Windows: 通常已预装
   - macOS: `brew install python-tk`
   - Linux: `sudo apt install python3-tk`
4. 下载 SUPIR 模型：
   - 从 [Hugging Face](https://huggingface.co/camenduru/SUPIR) 下载模型文件
   - 将模型文件放置在 `ComfyUI/models/supir` 目录下
5. 配置翻译功能（可选）：
   - 编辑 `config/translator.json` 文件
   - 填入百度翻译API密钥（已预设可用密钥）
6. 重启ComfyUI

## 使用说明

### 路径处理节点
1. 添加"Path Processor"节点
2. 设置输入路径和过滤条件
3. 选择批量/单文件模式
4. 节点将自动处理文件索引和图像加载
5. loop_index功能：
   - 在批量模式下自动递增
   - 可手动设置起始索引值
   - 支持多次队列执行时自动递增

### 队列触发节点
1. 添加"Queue Trigger"节点
2. 设置计数和总数
3. 节点将自动管理处理队列

### 模式切换节点
1. 添加"Work Mode"节点
2. 切换批量/单文件模式

### 目录选择器
1. 添加"Directory Picker"节点
2. 选择目录
3. 目录路径将被保存

### SUPIR 超分工作流
1. 添加"SUPIR Model Loader"节点并加载模型
2. 构建处理流程：
   - Encode → First Stage → Conditioner → Sample → Decode
3. 设置相应参数
4. 运行工作流进行超分处理

### 翻译功能
1. 在任意文本输入框中输入文字
2. 双击输入框触发翻译
3. 自动检测语言并进行翻译：
   - 中文文本将被翻译为英文
   - 英文文本将被翻译为中文
4. 翻译结果会自动替换原文本
5. 如遇到错误，请查看浏览器控制台

## 更新日志

### v1.01 (2024-01-08)
- 新增翻译功能
  - 支持双击翻译
  - 中英文自动检测
  - 集成百度翻译API
  - 添加防抖优化
  - 配置文件管理

### v1.00
- 初始版本发布
  - 实现文件处理工具
  - 实现SUPIR超分功能

## 贡献
欢迎提交Pull Request。对于重大更改，请先创建issue讨论。

## 许可证
[MIT](LICENSE)

---

# Axun Nodes - ComfyUI Plugin

[English version follows...]

[Previous English content remains unchanged]

import { app } from '../../scripts/app.js';
import { ApiService } from './web.js';

/**
 * LLM API端点配置
 */
export const API_ENDPOINTS = {
    "Silicon Cloud LLM": "/axun_nodes/llm/get_silicon_cloud_llm_models",
    "Silicon Cloud VLM": "/axun_nodes/llm/get_silicon_cloud_vlm_models",
    "Deepseek": "/axun_nodes/llm/get_deepseek_models"
};

/**
 * 场景预设参数
 */
export const SCENE_PRESETS = {
    "代码生成": {
        "Silicon Cloud LLM": {
            temperature: 0.0,
            top_p: 0.9
        },
        "Silicon Cloud VLM": {
            temperature: 0.0,
            top_p: 0.9
        },
        "Deepseek": {
            temperature: 0.0,
            top_p: 0.9
        }
    },
    "数学解题": {
        "Silicon Cloud LLM": {
            temperature: 0.0,
            top_p: 0.9
        },
        "Silicon Cloud VLM": {
            temperature: 0.0,
            top_p: 0.9
        },
        "Deepseek": {
            temperature: 0.0,
            top_p: 0.9
        }
    },
    "数据分析": {
        "Silicon Cloud LLM": {
            temperature: 1.0,
            top_p: 0.9
        },
        "Silicon Cloud VLM": {
            temperature: 1.0,
            top_p: 0.9
        },
        "Deepseek": {
            temperature: 1.0,
            top_p: 0.9
        }
    },
    "通用对话": {
        "Silicon Cloud LLM": {
            temperature: 1.3,
            top_p: 0.9
        },
        "Silicon Cloud VLM": {
            temperature: 1.3,
            top_p: 0.9
        },
        "Deepseek": {
            temperature: 1.3,
            top_p: 0.9
        }
    },
    "翻译": {
        "Silicon Cloud LLM": {
            temperature: 1.3,
            top_p: 0.9
        },
        "Silicon Cloud VLM": {
            temperature: 1.3,
            top_p: 0.9
        },
        "Deepseek": {
            temperature: 1.3,
            top_p: 0.9
        }
    },
    "创意写作": {
        "Silicon Cloud LLM": {
            temperature: 1.5,
            top_p: 0.95
        },
        "Silicon Cloud VLM": {
            temperature: 1.5,
            top_p: 0.95
        },
        "Deepseek": {
            temperature: 1.5,
            top_p: 0.95
        }
    }
};

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 获取LLM模型列表
 */
export async function fetchModels(provider) {
    console.log(`[LLM Debug - 模型获取] 开始获取模型列表，provider: ${provider}`);
    try {
        const endpoint = API_ENDPOINTS[provider];
        if (!endpoint) {
            console.error(`[LLM Debug - 模型获取] 未找到对应的endpoint: ${provider}`);
            return getDefaultModels(provider);
        }

        console.log(`[LLM Debug - 模型获取] 请求endpoint: ${endpoint}`);
        const response = await ApiService.fetchWithRetry(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
        });

        console.log(`[LLM Debug - 模型获取] API响应:`, response);
        if (Array.isArray(response) && response.length > 0) {
            console.log(`[LLM Debug - 模型获取] 成功获取模型列表:`, response);
            return response;
        } else {
            console.warn(`[LLM Debug - 模型获取] 返回空列表，使用默认模型`);
            return getDefaultModels(provider);
        }
    } catch (error) {
        if (error.message.includes('Unauthorized') || error.message.includes('Invalid API key')) {
            console.error(`[LLM Debug - 模型获取] API密钥无效:`, error);
            showApiKeyDialog(provider);
        }
        console.error(`[LLM Debug - 模型获取] 获取模型列表失败:`, error);
        return getDefaultModels(provider);
    }
}

/**
 * 获取默认模型列表
 */
function getDefaultModels(provider) {
    switch (provider) {
        case "Silicon Cloud LLM":
            return ["silicon-chat-v1"];
        case "Silicon Cloud VLM":
            return ["silicon-vl-chat-v1"];
        case "Deepseek":
            return ["deepseek-chat", "deepseek-coder"];
        default:
            return [];
    }
}

// 确保只初始化一次
if (!window.AXUN_LLM_INITIALIZED) {
    console.log("[LLM Debug] 开始初始化LLM模块...");
    window.AXUN_LLM_INITIALIZED = true;

    // 处理模型列表更新
    async function handleModelListUpdate(providerSelect, modelSelect) {
        if (!providerSelect || !modelSelect) {
            console.error("[LLM Debug] 选择器无效");
            return;
        }
        
        console.log("[LLM Debug] 开始更新模型列表");
        console.log("[LLM Debug] Provider:", providerSelect.value);
        console.log("[LLM Debug] 当前Model:", modelSelect.value);
        
        try {
            // 获取模型列表
            const models = await fetchModels(providerSelect.value);
            console.log("[LLM Debug] 获取到模型列表:", models);
            
            if (Array.isArray(models) && models.length > 0) {
                // 保存当前值
                const currentValue = modelSelect.value || models[0];
                console.log("[LLM Debug] 当前/默认值:", currentValue);
                
                // 更新选项
                modelSelect.innerHTML = "";
                models.forEach(model => {
                    const option = document.createElement("option");
                    option.value = model;
                    option.textContent = model;
                    modelSelect.appendChild(option);
                });
                
                // 设置值
                if (models.includes(currentValue)) {
                    modelSelect.value = currentValue;
                } else {
                    modelSelect.value = models[0];
                }
                console.log("[LLM Debug] 设置新值:", modelSelect.value);
                
                // 触发更新事件
                const event = new Event("change", { bubbles: true });
                modelSelect.dispatchEvent(event);
                modelSelect.dispatchEvent(new Event("input", { bubbles: true }));
                
                console.log("[LLM Debug] 模型列表更新完成");
            } else {
                console.warn("[LLM Debug] 获取到空模型列表，使用默认值");
                const defaultModels = getDefaultModels(providerSelect.value);
                if (defaultModels.length > 0) {
                    modelSelect.innerHTML = "";
                    defaultModels.forEach(model => {
                        const option = document.createElement("option");
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    });
                    modelSelect.value = defaultModels[0];
                    
                    // 触发更新事件
                    const event = new Event("change", { bubbles: true });
                    modelSelect.dispatchEvent(event);
                    modelSelect.dispatchEvent(new Event("input", { bubbles: true }));
                }
            }
        } catch (error) {
            console.error("[LLM Debug] 更新模型列表失败:", error);
            // 使用默认值
            const defaultModels = getDefaultModels(providerSelect.value);
            if (defaultModels.length > 0) {
                modelSelect.innerHTML = "";
                defaultModels.forEach(model => {
                    const option = document.createElement("option");
                    option.value = model;
                    option.textContent = model;
                    modelSelect.appendChild(option);
                });
                modelSelect.value = defaultModels[0];
                
                // 触发更新事件
                const event = new Event("change", { bubbles: true });
                modelSelect.dispatchEvent(event);
                modelSelect.dispatchEvent(new Event("input", { bubbles: true }));
            }
        }
    }

    // 设置 LLM 节点观察者
    function setupLLMObserver() {
        console.log("[LLM Debug] 设置LLM观察者...");
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.classList && node.classList.contains("comfy-node")) {
                        const nodeType = node.querySelector(".nodename");
                        if (nodeType && nodeType.textContent === "LLM Assistant") {
                            console.log("[LLM Debug] 发现新的LLM节点，设置事件监听...");
                            setupLLMNodeEvents(node);
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        console.log("[LLM Debug] LLM观察者设置完成");
    }

    // 设置 LLM 节点事件
    function setupLLMNodeEvents(node) {
        // 避免重复绑定
        if (node.dataset.llmInitialized) {
            console.log("[LLM Debug] 节点已初始化，跳过");
            return;
        }
        node.dataset.llmInitialized = "true";
        
        // 获取 widgets
        const widgets = node.querySelectorAll(".comfy-widget");
        const providerWidget = Array.from(widgets).find(w => w.dataset.name === "provider");
        const modelWidget = Array.from(widgets).find(w => w.dataset.name === "model");
        
        if (providerWidget && modelWidget) {
            console.log("[LLM Debug] 找到provider和model widgets");
            
            // 获取实际的select元素
            const providerSelect = providerWidget.querySelector("select");
            const modelSelect = modelWidget.querySelector("select");
            
            if (providerSelect && modelSelect) {
                // 使用防抖处理变更事件
                const debouncedUpdate = debounce(() => {
                    handleModelListUpdate(providerSelect, modelSelect);
                }, 300);
                
                // 监听 provider 变化
                providerSelect.addEventListener("change", (e) => {
                    console.log("[LLM Debug] Provider变更事件触发:", e.target.value);
                    debouncedUpdate();
                });
                
                // 初始化获取模型列表
                console.log("[LLM Debug] 初始化模型列表");
                handleModelListUpdate(providerSelect, modelSelect);
            } else {
                console.error("[LLM Debug] 未找到select元素");
            }
        } else {
            console.error("[LLM Debug] 未找到widgets");
        }
    }

    // 初始化
    setupLLMObserver();
}

// LLM节点扩展
app.registerExtension({
    name: "AxunNodes.LLM",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass !== 'axun_nodes_LLM') return;
        
        console.log("[LLM Debug] 开始注册LLM节点");
        
        // 保存原始的INPUT_TYPES
        const origInputTypes = nodeType.INPUT_TYPES;
        
        // 重写INPUT_TYPES
        nodeType.INPUT_TYPES = function() {
            console.log("[LLM Debug] 调用INPUT_TYPES");
            const inputTypes = origInputTypes();
            return inputTypes;
        };

        // 添加节点创建回调
        const origNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            console.log("[LLM Debug] 节点创建开始");
            if (origNodeCreated) {
                origNodeCreated.apply(this, arguments);
            }

            const node = this;
            console.log("[LLM Debug] 节点实例:", node);

            // 获取 widgets
            const providerWidget = node.widgets.find(w => w.name === "provider");
            const modelWidget = node.widgets.find(w => w.name === "model");

            if (providerWidget && modelWidget) {
                console.log("[LLM Debug] 找到 provider 和 model widgets");

                // 保存原始的 callback
                const origProviderCallback = providerWidget.callback;
                
                // 重写 provider 的 callback
                providerWidget.callback = function() {
                    console.log("[LLM Debug] Provider callback 触发");
                    console.log("[LLM Debug] 当前 Provider:", this.value);
                    
                    // 调用原始 callback
                    if (origProviderCallback) {
                        origProviderCallback.apply(this, arguments);
                    }

                    // 从 INPUT_TYPES 获取对应的模型列表
                    const inputTypes = origInputTypes();
                    const providerModels = inputTypes.required.model[0];
                    console.log("[LLM Debug] 当前Provider的模型列表:", providerModels);
                    
                    // 更新 model widget
                    if (Array.isArray(providerModels) && providerModels.length > 0) {
                        modelWidget.options.values = providerModels;
                        
                        // 如果当前值不在列表中，设置为第一个值
                        if (!providerModels.includes(modelWidget.value)) {
                            modelWidget.value = providerModels[0];
                        }
                        
                        // 触发 model widget 的更新
                        if (modelWidget.callback) {
                            modelWidget.callback(modelWidget.value);
                        }
                        
                        // 通知节点更新
                        node.onWidgetChanged(modelWidget);
                        console.log("[LLM Debug] 模型列表更新完成");
                    } else {
                        console.warn("[LLM Debug] 未找到有效的模型列表");
                    }
                };

                // 初始化时触发一次更新
                providerWidget.callback.call(providerWidget);
            }
        };
    }
}); 
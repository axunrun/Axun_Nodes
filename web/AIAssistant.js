import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

// 为通用 OpenAI 节点创建带有 base_url 和 api_key 参数的模型获取扩展
const createGenericOpenAIExtension = (nodeName) => {
    return {
        name: `axun.AIAssistant.${nodeName.toLowerCase()}.api.model_fetch`,
        async beforeRegisterNodeDef(nodeType, nodeData, app) {
            if (nodeData.name === nodeName) {
                const originalNodeCreated = nodeType.prototype.onNodeCreated;
                
                nodeType.prototype.onNodeCreated = async function () {
                    if (originalNodeCreated) {
                        originalNodeCreated.apply(this, arguments);
                    }

                    const configSelectionWidget = this.widgets.find((w) => w.name === "config_selection");
                    const modelWidget = this.widgets.find((w) => w.name === "model");
                    const baseUrlWidget = this.widgets.find((w) => w.name === "base_url");
                    const apiKeyWidget = this.widgets.find((w) => w.name === "api_key");
                    
                    if (!modelWidget || !baseUrlWidget || !apiKeyWidget) {
                        console.warn("[AIAssistant] 未找到必要的 widgets");
                        return;
                    }

                    // 初始模型列表
                    if (!modelWidget.options.values || modelWidget.options.values.length === 0) {
                        modelWidget.options.values = ["请输入 API Key 和 Base URL 后点击刷新按钮获取模型列表"];
                        modelWidget.value = modelWidget.options.values[0];
                    }

                    // 处理配置选择变化
                    if (configSelectionWidget) {
                        const originalConfigSelectionCallback = configSelectionWidget.callback;
                        configSelectionWidget.callback = function(value) {
                            if (originalConfigSelectionCallback) {
                                originalConfigSelectionCallback.apply(this, arguments);
                            }
                            
                            // 当选择"手动输入"时不做任何改变
                            if (value === "手动输入") {
                                return;
                            }
                            
                            // 根据选择的配置自动填充API信息
                            fetch("/axun/AIAssistant/load_config", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    config_name: value
                                }),
                            })
                            .then(response => response.json())
                            .then(config => {
                                if (config.base_url) {
                                    baseUrlWidget.value = config.base_url;
                                }
                                if (config.api_key) {
                                    apiKeyWidget.value = config.api_key;
                                }
                                app.graph.setDirtyCanvas(true);
                            })
                            .catch(error => {
                                console.error("[AIAssistant] 加载配置失败:", error);
                            });
                        };
                    }

                    // 每当 base_url 或 api_key 更改时，添加刷新按钮
                    const addRefreshButton = () => {
                        // 确保只添加一次刷新按钮
                        const existingRefreshButton = this.widgets.find(w => w.name === "refresh_models");
                        if (existingRefreshButton) return;
                        
                        // 创建刷新按钮
                        const refreshButton = this.addWidget("button", "刷新模型列表", "refresh_models", () => {
                            fetchAndUpdateModels();
                        });
                        
                        // 重新排序widgets，确保按钮在合适的位置
                        this.widgets = this.widgets.sort((a, b) => {
                            if (a.name === "config_selection") return -5;
                            if (a.name === "base_url") return -4;
                            if (a.name === "api_key") return -3;
                            if (a.name === "refresh_models") return -2;
                            if (a.name === "model") return -1;
                            return 1;
                        });
                    };

                    const fetchAndUpdateModels = async () => {
                        try {
                            // 检查是否有 base_url 和 api_key
                            if (!baseUrlWidget.value || !apiKeyWidget.value) {
                                modelWidget.options.values = ["请先填写 API Key 和 Base URL"];
                                modelWidget.value = modelWidget.options.values[0];
                                app.graph.setDirtyCanvas(true);
                                return;
                            }

                            // 显示加载中状态
                            modelWidget.options.values = ["正在获取模型列表..."];
                            modelWidget.value = modelWidget.options.values[0];
                            app.graph.setDirtyCanvas(true);

                            // 从自定义 API 获取模型列表
                            console.debug(`[AIAssistant] 开始获取 ${nodeName} 模型列表...`);
                            const response = await fetch("/axun/AIAssistant/generic_openai/models", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    base_url: baseUrlWidget.value,
                                    api_key: apiKeyWidget.value
                                }),
                            });

                            if (response.ok) {
                                const models = await response.json();
                                console.debug(`[AIAssistant] 获取模型列表成功:`, models);
                                
                                const prevValue = modelWidget.value;
                                modelWidget.options.values = models;
                                
                                if (prevValue && models.includes(prevValue)) {
                                    modelWidget.value = prevValue;
                                } else if (models.length > 0) {
                                    modelWidget.value = models[0];
                                }
                            } else {
                                console.error(`[AIAssistant] 获取模型列表失败: ${response.status}`);
                                modelWidget.options.values = ["获取模型列表失败"];
                                modelWidget.value = modelWidget.options.values[0];
                            }
                            
                            app.graph.setDirtyCanvas(true);
                        } catch (error) {
                            console.error(`[AIAssistant] 获取模型列表出错:`, error);
                            modelWidget.options.values = ["获取模型列表失败: " + error.message];
                            modelWidget.value = modelWidget.options.values[0];
                            app.graph.setDirtyCanvas(true);
                        }
                    };

                    // 设置监听器
                    const setupWidgetListeners = () => {
                        // 为 base_url 和 api_key 添加更改监听器
                        const originalOnChange = baseUrlWidget.callback;
                        baseUrlWidget.callback = function(v, index, e) {
                            if (originalOnChange) originalOnChange.call(this, v, index, e);
                            // 自动去除尾部斜杠
                            if (v.endsWith("/")) {
                                baseUrlWidget.value = v.slice(0, -1);
                            }
                        };
                    };
                    
                    // 添加刷新按钮
                    addRefreshButton();
                    
                    // 设置监听器
                    setupWidgetListeners();
                };
            }
        },
    };
};

// 通用 OpenAI LLM 扩展
app.registerExtension(
    createGenericOpenAIExtension("GenericOpenAILLMAPI")
);

// 通用 OpenAI VLM 扩展
app.registerExtension(
    createGenericOpenAIExtension("GenericOpenAIVLMAPI")
);

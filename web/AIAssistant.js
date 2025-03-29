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

                    // 强制刷新配置列表
                    // 这会发送一个请求到服务器，获取所有已保存的配置
                    const fetchConfigList = async () => {
                        try {
                            // 发送一个空请求，只是为了触发后端的配置加载，打印日志
                            await fetch("/axun/AIAssistant/load_config", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({
                                    config_name: "手动输入" // 这个名称肯定不存在，但会触发配置列表加载
                                }),
                            });
                            
                            console.log("[AIAssistant] 强制刷新配置列表完成");
                            
                            // 这里我们不处理响应，因为我们只想触发服务器日志，查看配置是否被正确加载
                        } catch (error) {
                            console.warn("[AIAssistant] 刷新配置列表失败:", error);
                        }
                    };
                    
                    // 执行配置刷新
                    fetchConfigList();

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
                            
                            console.log(`[AIAssistant] 选择配置: ${value}`);
                            
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
                                console.log(`[AIAssistant] 成功加载配置:`, config);
                                
                                // 填充基本API信息
                                if (config.base_url) {
                                    baseUrlWidget.value = config.base_url;
                                }
                                if (config.api_key) {
                                    apiKeyWidget.value = config.api_key;
                                }
                                
                                // 填充其他参数
                                const systemPromptWidget = this.widgets.find(w => w.name === "system_prompt");
                                const userPromptWidget = this.widgets.find(w => w.name === "user_prompt");
                                const maxTokensWidget = this.widgets.find(w => w.name === "max_tokens");
                                const temperatureWidget = this.widgets.find(w => w.name === "temperature");
                                const topPWidget = this.widgets.find(w => w.name === "top_p");
                                
                                // 对找到的widget记录日志
                                console.log(`[AIAssistant] 找到的widgets:`, {
                                    systemPrompt: !!systemPromptWidget, 
                                    userPrompt: !!userPromptWidget,
                                    maxTokens: !!maxTokensWidget,
                                    temperature: !!temperatureWidget,
                                    topP: !!topPWidget
                                });
                                
                                // 如果有model值并且在列表中存在，则设置
                                if (config.model && modelWidget && modelWidget.options.values.includes(config.model)) {
                                    modelWidget.value = config.model;
                                }
                                
                                // 设置其他参数 - 添加明确的日志
                                if (config.system_prompt && systemPromptWidget) {
                                    console.log(`[AIAssistant] 设置system_prompt: ${config.system_prompt.substring(0, 20)}...`);
                                    systemPromptWidget.value = config.system_prompt;
                                } else if (config.system_prompt) {
                                    console.warn(`[AIAssistant] 配置有system_prompt但未找到对应widget`);
                                }
                                
                                if (config.user_prompt && userPromptWidget) {
                                    console.log(`[AIAssistant] 设置user_prompt: ${config.user_prompt.substring(0, 20)}...`);
                                    userPromptWidget.value = config.user_prompt;
                                } else if (config.user_prompt) {
                                    console.warn(`[AIAssistant] 配置有user_prompt但未找到对应widget`);
                                }
                                
                                if (config.max_tokens !== undefined && maxTokensWidget) {
                                    maxTokensWidget.value = config.max_tokens;
                                }
                                if (config.temperature !== undefined && temperatureWidget) {
                                    temperatureWidget.value = config.temperature;
                                }
                                if (config.top_p !== undefined && topPWidget) {
                                    topPWidget.value = config.top_p;
                                }
                                
                                // VLM节点特有的详细度参数
                                const detailWidget = this.widgets.find(w => w.name === "detail");
                                if (config.detail && detailWidget) {
                                    detailWidget.value = config.detail;
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

import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

const createModelFetchExtension = (nodeName, endpoint) => {
    return {
        name: `axun.AIAssistant.${nodeName.toLowerCase()}.api.model_fetch`,
        async beforeRegisterNodeDef(nodeType, nodeData, app) {
            if (nodeData.name === nodeName) {
                const originalNodeCreated = nodeType.prototype.onNodeCreated;
                nodeType.prototype.onNodeCreated = async function () {
                    if (originalNodeCreated) {
                        originalNodeCreated.apply(this, arguments);
                    }

                    const modelWidget = this.widgets.find((w) => w.name === "model");
                    if (!modelWidget) {
                        console.warn("[AIAssistant] 未找到model widget");
                        return;
                    }

                    const fetchModels = async () => {
                        try {
                            console.debug(`[AIAssistant] 开始获取${nodeName}模型列表...`);
                            const response = await fetch(endpoint, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                body: JSON.stringify({}),
                            });

                            if (response.ok) {
                                const models = await response.json();
                                console.debug(`[AIAssistant] 获取${nodeName}模型列表成功:`, models);
                                return models;
                            } else {
                                console.error(`[AIAssistant] 获取${nodeName}模型列表失败: ${response.status}`);
                                return ["获取模型列表失败"];
                            }
                        } catch (error) {
                            console.error(`[AIAssistant] 获取${nodeName}模型列表出错:`, error);
                            return ["获取模型列表失败"];
                        }
                    };

                    const updateModels = async () => {
                        const prevValue = modelWidget.value;
                        modelWidget.value = "";
                        modelWidget.options.values = [];

                        const models = await fetchModels();
                        
                        modelWidget.options.values = models;
                        console.debug(`[AIAssistant] 更新${nodeName}模型列表:`, models);

                        if (models.includes(prevValue)) {
                            modelWidget.value = prevValue;
                        } else if (models.length > 0) {
                            modelWidget.value = models[0];
                        }

                        app.graph.setDirtyCanvas(true);
                    };

                    await updateModels();
                };
            }
        },
    };
};

// LLM Extension
app.registerExtension(
    createModelFetchExtension(
        "SiliconCloudLLMAPI",
        "/axun/AIAssistant/llm/models"
    )
);

// VLM Extension
app.registerExtension(
    createModelFetchExtension(
        "SiliconCloudVLMAPI",
        "/axun/AIAssistant/vlm/models"
    )
);

// DeepSeek LLM Extension
app.registerExtension(
    createModelFetchExtension(
        "DeepSeekLLMAPI",
        "/axun/AIAssistant/deepseek/models"
    )
);
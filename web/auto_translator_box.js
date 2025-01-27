import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// 防抖函数
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

app.registerExtension({
    name: "Comfy.Translator.AutoTranslatorBox",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "AutoTranslatorBox") {
            // 扩展节点的默认行为
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);
                
                // 设置节点的大小
                this.size = [400, 250];
                
                // 调整文本框样式
                requestAnimationFrame(() => {
                    if (this.widgets) {
                        // 输入文本框
                        const inputWidget = this.widgets[0];
                        if (inputWidget?.element) {
                            const inputTextarea = inputWidget.element.querySelector("textarea");
                            if (inputTextarea) {
                                inputTextarea.style.height = "80px";
                            }
                        }
                        
                        // 翻译结果文本框
                        const translatedWidget = this.widgets[1];
                        if (translatedWidget?.element) {
                            const translatedTextarea = translatedWidget.element.querySelector("textarea");
                            if (translatedTextarea) {
                                translatedTextarea.style.height = "80px";
                                translatedTextarea.style.backgroundColor = "#222";
                                translatedTextarea.style.color = "#fff";
                                translatedTextarea.style.marginTop = "10px";
                            }
                        }
                    }
                });
                
                // 监听文本变化
                const originalCallback = this.widgets[0].callback;
                this.widgets[0].callback = async () => {
                    if (originalCallback) {
                        originalCallback.call(this);
                    }
                    
                    // 触发节点执行
                    await app.graph.runAsyncOnBackgroundThread(async () => {
                        const node = this;
                        await app.queuePrompt(0, 1, { nodes: [node] });
                    });
                };
            };
            
            // 处理节点反馈
            const onNodeFeedback = nodeType.prototype.onNodeFeedback;
            nodeType.prototype.onNodeFeedback = function(message) {
                onNodeFeedback?.apply(this, arguments);
                
                if (message?.widget_name === "translated" && message?.value) {
                    this.widgets[1].value = message.value;
                    this.setDirtyCanvas(true);
                }
            };
        }
    }
}); 
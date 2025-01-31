import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Comfy.StoryExtractor",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "StoryExtractor") {
            // 扩展节点的默认行为
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);
                
                // 调整文本框大小
                requestAnimationFrame(() => {
                    if (this.widgets) {
                        // 输入文本框
                        const inputWidget = this.widgets[0];
                        if (inputWidget?.element) {
                            const inputTextarea = inputWidget.element.querySelector("textarea");
                            if (inputTextarea) {
                                inputTextarea.style.height = "150px";
                                inputTextarea.style.width = "100%";
                                inputTextarea.style.boxSizing = "border-box";
                            }
                        }
                        
                        // 显示文本框
                        const outputWidget = this.widgets[1];
                        if (outputWidget?.element) {
                            const outputTextarea = outputWidget.element.querySelector("textarea");
                            if (outputTextarea) {
                                outputTextarea.style.height = "200px";
                                outputTextarea.style.width = "100%";
                                outputTextarea.style.boxSizing = "border-box";
                                outputTextarea.style.backgroundColor = "#1a1a1a";
                                outputTextarea.style.color = "#ffffff";
                                outputTextarea.style.marginTop = "10px";
                                outputTextarea.style.padding = "5px";
                                outputTextarea.style.resize = "vertical";
                                outputTextarea.style.fontFamily = "monospace";
                                outputTextarea.readOnly = true;
                            }
                        }
                    }
                });
            };
            
            // 处理节点反馈
            const onNodeFeedback = nodeType.prototype.onNodeFeedback;
            nodeType.prototype.onNodeFeedback = function(message) {
                onNodeFeedback?.apply(this, arguments);
                
                if (message?.widget_name === "extracted_text" && message?.value) {
                    const widget = this.widgets.find(w => w.name === "extracted_text");
                    if (widget) {
                        widget.value = message.value;
                        const textarea = widget.element.querySelector("textarea");
                        if (textarea) {
                            textarea.value = message.value;
                        }
                        this.setDirtyCanvas(true);
                    }
                }
            };
        }
    }
}); 
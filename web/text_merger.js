import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "Comfy.AIAssistant.TextMerger",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "TextMerger") {
            // 扩展节点的默认行为
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);
                
                // 设置节点的固定大小
                this.size = [200, 120];
            };
        }
    }
}); 
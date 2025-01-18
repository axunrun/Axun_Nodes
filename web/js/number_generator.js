import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 注册节点
app.registerExtension({
    name: "Axun.NumberGenerator",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === 'NumberGenerator') {
            // 设置节点分类
            nodeType.category = "!Axun Nodes/AIAssistant";
            
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);
                
                const node = this;
                
                // 获取控件
                const numberValueWidget = node.widgets.find(w => w.name === 'number_value');
                
                // 调整控件顺序
                const widgets = node.widgets;
                const prefixWidget = widgets.find(w => w.name === 'prefix_text');
                const middleWidget = widgets.find(w => w.name === 'middle_text');
                const numberWidget = widgets.find(w => w.name === 'number_value');
                
                if (prefixWidget && middleWidget && numberWidget) {
                    // 确保控件顺序：prefix -> middle -> number
                    const prefixIndex = widgets.indexOf(prefixWidget);
                    const middleIndex = widgets.indexOf(middleWidget);
                    const numberIndex = widgets.indexOf(numberWidget);
                    
                    // 调整middle_text位置
                    if (middleIndex > numberIndex) {
                        widgets.splice(middleIndex, 1);
                        widgets.splice(prefixIndex + 1, 0, middleWidget);
                    }
                }
                
                if (numberValueWidget) {
                    // 从后端获取初始值
                    fetch(`/axun-number/get-value?id=${node.id}`)
                        .then(r => r.json())
                        .then(data => {
                            if (data.number_value) {
                                numberValueWidget.value = data.number_value;
                                node.onWidgetChanged(numberValueWidget);
                            }
                        });

                    // 添加callback同步到后端
                    numberValueWidget.callback = async function() {
                        await fetch(
                            `/axun-number/set-value?id=${node.id}&value=${numberValueWidget.value}`,
                            {method: 'POST'}
                        );
                        node.onWidgetChanged(numberValueWidget);
                    }
                }
            };
        }
    }
}); 
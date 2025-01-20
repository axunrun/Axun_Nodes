import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

// 注册文本处理器扩展
app.registerExtension({
    name: "AxunNodes.TextProcessor",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === 'TextProcessor') {
            // 设置节点分类
            nodeType.category = "!Axun Nodes/AIAssistant";
            
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);
                
                const node = this;
                
                // 获取text_index控件
                const textIndexWidget = node.widgets.find(w => w.name === 'text_index');
                if (textIndexWidget) {
                    console.log("[TextProcessor] 找到text_index控件");
                    
                    // 从后端获取初始索引
                    fetch(`/axun-text/text-index?id=${node.id}`)
                        .then(r => r.json())
                        .then(data => {
                            console.log("[TextProcessor] 获取初始索引:", data);
                            textIndexWidget.value = Math.floor(parseInt(data.text_index) || 1);
                            node.onWidgetChanged(textIndexWidget);
                        })
                        .catch(err => console.error("[TextProcessor] 获取索引失败:", err));

                    // 添加callback同步到后端
                    textIndexWidget.callback = async function() {
                        console.log("[TextProcessor] 索引变更:", textIndexWidget.value);
                        await fetch(
                            `/axun-text/set-text-index?id=${node.id}&index=${Math.floor(textIndexWidget.value)}`,
                            {method: 'POST'}
                        );
                        node.onWidgetChanged(textIndexWidget);
                    }

                    // 监听executed事件，更新索引
                    api.addEventListener('executed', async () => {
                        console.log("[TextProcessor] 执行完成，检查索引更新");
                        const response = await fetch(`/axun-text/text-index?id=${node.id}`);
                        const data = await response.json();
                        if (data.text_index !== textIndexWidget.value) {
                            console.log("[TextProcessor] 更新索引:", data.text_index);
                            textIndexWidget.value = data.text_index;
                            node.onWidgetChanged(textIndexWidget);
                        }
                    });

                    // 监听queue事件
                    api.addEventListener('queue', () => {
                        console.log("[TextProcessor] 队列执行，同步索引");
                        node.onWidgetChanged(textIndexWidget);
                    });
                }
                
                // 调整控件顺序
                const widgets = node.widgets;
                const appstartTextWidget = widgets.find(w => w.name === 'appstart_text');
                const sampleTextWidget = widgets.find(w => w.name === 'sample_text');
                const characterAWidget = widgets.find(w => w.name === 'character_a_preset');
                const characterBWidget = widgets.find(w => w.name === 'character_b_preset');
                const characterCWidget = widgets.find(w => w.name === 'character_c_preset');
                
                // 重新排序控件
                const orderedWidgets = [];
                
                // 添加角色预设控件
                if (characterAWidget) orderedWidgets.push(characterAWidget);
                if (characterBWidget) orderedWidgets.push(characterBWidget);
                if (characterCWidget) orderedWidgets.push(characterCWidget);
                
                // 添加其他控件
                if (appstartTextWidget) orderedWidgets.push(appstartTextWidget);
                if (sampleTextWidget) orderedWidgets.push(sampleTextWidget);
                
                // 添加剩余的控件
                widgets.forEach(widget => {
                    if (!orderedWidgets.includes(widget)) {
                        orderedWidgets.push(widget);
                    }
                });
                
                // 更新节点的控件顺序
                node.widgets = orderedWidgets;
            };
        }
    }
}); 
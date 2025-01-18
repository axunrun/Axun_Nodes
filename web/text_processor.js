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
                    // 从后端获取初始索引
                    fetch(`/axun-text/text-index?id=${node.id}`)
                        .then(r => r.json())
                        .then(data => {
                            textIndexWidget.value = Math.floor(parseInt(data.text_index) || 1);
                            node.onWidgetChanged(textIndexWidget);
                        });

                    // 添加callback同步到后端
                    textIndexWidget.callback = async function() {
                        await fetch(
                            `/axun-text/set-text-index?id=${node.id}&index=${Math.floor(textIndexWidget.value)}`,
                            {method: 'POST'}
                        );
                        node.onWidgetChanged(textIndexWidget);
                    }

                    // 添加afterQueued回调
                    textIndexWidget.afterQueued = () => {
                        // 不再自动递增，让后端处理
                        node.onWidgetChanged(textIndexWidget);
                    }

                    // 监听executed事件
                    api.addEventListener('executed', async () => {
                        const response = await fetch(`/axun-text/text-index?id=${node.id}`);
                        const data = await response.json();
                        if (data.text_index !== textIndexWidget.value) {
                            textIndexWidget.value = data.text_index;
                            node.onWidgetChanged(textIndexWidget);
                        }
                    });

                    // 监听queue事件
                    api.addEventListener('queue', () => {
                        node.onWidgetChanged(textIndexWidget);
                    });
                }
                
                // 调整文本框顺序
                const widgets = node.widgets;
                const appstartTextWidget = widgets.find(w => w.name === 'appstart_text');
                const sampleTextWidget = widgets.find(w => w.name === 'sample_text');
                
                if (appstartTextWidget && sampleTextWidget) {
                    // 确保 appstart_text 在 sample_text 之前
                    const appstartIndex = widgets.indexOf(appstartTextWidget);
                    const sampleIndex = widgets.indexOf(sampleTextWidget);
                    if (appstartIndex > sampleIndex) {
                        widgets.splice(appstartIndex, 1);
                        widgets.splice(sampleIndex, 0, appstartTextWidget);
                    }
                }
            };
        }
    }
}); 
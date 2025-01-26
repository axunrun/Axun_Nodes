import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

// 注册文本缓存器扩展
app.registerExtension({
    name: "AxunNodes.TextCache",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === 'TextCache') {
            // 设置节点分类
            nodeType.category = "!Axun Nodes/AIAssistant";
            
            // 保存原始的onNodeCreated函数
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            
            // 添加onExecuted处理
            nodeType.prototype.onExecuted = function(message) {
                console.log("[TextCache] 节点执行，收到消息:", message);
                
                const node = this;
                const inputTextWidget = node.widgets.find(w => w.name === 'input_text');
                const cacheTextWidget = node.widgets.find(w => w.name === 'cache_text');
                
                // 检查是否有输入连接
                const inputLink = node.inputs[0]?.link;
                console.log("[TextCache] 输入连接状态:", inputLink);
                
                // 如果有输入值，更新到缓存
                if (message?.output?.input_text !== undefined) {
                    const inputText = message.output.input_text;
                    console.log("[TextCache] 收到输入文本:", inputText);
                    
                    // 更新输入控件
                    if (inputTextWidget) {
                        inputTextWidget.value = inputText;
                        node.onWidgetChanged(inputTextWidget);
                    }
                    
                    // 更新缓存控件
                    if (cacheTextWidget) {
                        cacheTextWidget.value = inputText;
                        node.onWidgetChanged(cacheTextWidget);
                        
                        // 同步到后端
                        fetch(
                            `/axun-text/set-cache?id=${node.id}`,
                            {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: inputText })
                            }
                        ).catch(err => console.error("[TextCache] 设置缓存失败:", err));
                    }
                }
            };
            
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);
                
                const node = this;
                console.log("[TextCache] 节点创建");
                
                // 获取所有控件
                const widgets = node.widgets;
                const inputTextWidget = widgets.find(w => w.name === 'input_text');
                const cacheTextWidget = widgets.find(w => w.name === 'cache_text');
                
                if (inputTextWidget) {
                    console.log("[TextCache] 找到输入文本控件");
                    
                    // 添加输入文本的callback
                    inputTextWidget.callback = async function() {
                        console.log("[TextCache] 输入文本变更:", inputTextWidget.value);
                        if (cacheTextWidget && inputTextWidget.value) {
                            cacheTextWidget.value = inputTextWidget.value;
                            node.onWidgetChanged(cacheTextWidget);
                            
                            // 同步到后端
                            try {
                                await fetch(
                                    `/axun-text/set-cache?id=${node.id}`,
                                    {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ text: inputTextWidget.value })
                                    }
                                );
                            } catch (err) {
                                console.error("[TextCache] 设置缓存失败:", err);
                            }
                        }
                    }
                }
                
                if (cacheTextWidget) {
                    console.log("[TextCache] 找到缓存文本控件");
                    
                    // 从后端获取初始缓存
                    fetch(`/axun-text/get-cache?id=${node.id}`)
                        .then(r => r.json())
                        .then(data => {
                            console.log("[TextCache] 获取初始缓存:", data);
                            if (data.text) {
                                cacheTextWidget.value = data.text;
                                node.onWidgetChanged(cacheTextWidget);
                            }
                        })
                        .catch(err => console.error("[TextCache] 获取缓存失败:", err));

                    // 添加缓存文本的callback
                    cacheTextWidget.callback = async function() {
                        console.log("[TextCache] 缓存文本变更:", cacheTextWidget.value);
                        try {
                            await fetch(
                                `/axun-text/set-cache?id=${node.id}`,
                                {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ text: cacheTextWidget.value })
                                }
                            );
                            node.onWidgetChanged(cacheTextWidget);
                        } catch (err) {
                            console.error("[TextCache] 设置缓存失败:", err);
                        }
                    }
                }
                
                // 重新排序控件
                const orderedWidgets = [];
                
                // 添加输入文本控件
                if (inputTextWidget) orderedWidgets.push(inputTextWidget);
                if (cacheTextWidget) orderedWidgets.push(cacheTextWidget);
                
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
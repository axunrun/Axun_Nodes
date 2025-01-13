import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

// 预设管理服务
class PresetService {
    // 获取预设列表
    static async getPresets() {
        try {
            const response = await api.fetchApi("/axun/AIAssistant/presets", {
                method: "POST"
            });
            const presets = await response.json();
            return presets;
        } catch (error) {
            console.error("[AIAssistant] 获取预设列表失败:", error);
            return ["获取预设列表失败"];
        }
    }

    // 保存预设
    static async savePreset(preset) {
        try {
            const response = await api.fetchApi("/axun/AIAssistant/save_preset", {
                method: "POST",
                body: JSON.stringify(preset)
            });
            const result = await response.json();
            return result.status === "success";
        } catch (error) {
            console.error("[AIAssistant] 保存预设失败:", error);
            return false;
        }
    }

    // 删除预设
    static async deletePreset(presetName) {
        try {
            const response = await api.fetchApi("/axun/AIAssistant/delete_preset", {
                method: "POST",
                body: JSON.stringify({ name: presetName })
            });
            const result = await response.json();
            return result.status === "success";
        } catch (error) {
            console.error("[AIAssistant] 删除预设失败:", error);
            return false;
        }
    }
}

// 注册预设节点
app.registerExtension({
    name: "axun.AIAssistant.preset",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "AIAssistantPreset") {
            // 保存原始的onNodeCreated
            const originalNodeCreated = nodeType.prototype.onNodeCreated;
            
            // 重写onNodeCreated
            nodeType.prototype.onNodeCreated = async function() {
                if (originalNodeCreated) {
                    originalNodeCreated.apply(this, arguments);
                }

                const node = this;
                
                // 获取预设选择控件
                const presetWidget = node.widgets.find(w => w.name === "preset");
                if (!presetWidget) {
                    console.warn("[AIAssistant] 未找到preset widget");
                    return;
                }

                // 更新预设列表
                const updatePresets = async () => {
                    const prevValue = presetWidget.value;
                    presetWidget.value = "";
                    presetWidget.options.values = [];

                    const presets = await PresetService.getPresets();
                    
                    presetWidget.options.values = presets;
                    console.debug("[AIAssistant] 更新预设列表:", presets);

                    if (presets.includes(prevValue)) {
                        presetWidget.value = prevValue;
                    } else if (presets.length > 0) {
                        presetWidget.value = presets[0];
                    }

                    app.graph.setDirtyCanvas(true);
                };

                // 添加删除预设按钮
                node.addWidget("button", "删除预设", null, async () => {
                    const currentPreset = presetWidget.value;
                    if (!currentPreset) {
                        alert("请先选择要删除的预设");
                        return;
                    }

                    if (currentPreset === "通用对话") {
                        alert("默认预设不能删除");
                        return;
                    }

                    if (!confirm(`确定要删除预设"${currentPreset}"吗？此操作不可恢复。`)) {
                        return;
                    }

                    const success = await PresetService.deletePreset(currentPreset);
                    if (success) {
                        await updatePresets();
                    } else {
                        alert("删除预设失败");
                    }
                });

                // 添加新建预设按钮
                node.addWidget("button", "新建预设", null, () => {
                    // 创建对话框
                    const dialog = document.createElement("dialog");
                    dialog.style.padding = "20px";
                    dialog.style.borderRadius = "8px";
                    dialog.style.backgroundColor = "#2d2d2d";
                    dialog.style.color = "#ffffff";
                    dialog.style.border = "1px solid #666";
                    dialog.style.minWidth = "400px";
                    
                    dialog.innerHTML = `
                        <h3 style="margin-top: 0;">新建预设</h3>
                        <form method="dialog" style="display: flex; flex-direction: column; gap: 15px;">
                            <div>
                                <label>预设名称:</label>
                                <input type="text" id="preset-name" required 
                                    style="width: 100%; padding: 5px; background: #333; border: 1px solid #666; color: #fff; border-radius: 4px;">
                            </div>
                            <div>
                                <label>系统提示词:</label>
                                <textarea id="system-prompt" rows="5" 
                                    style="width: 100%; padding: 5px; background: #333; border: 1px solid #666; color: #fff; border-radius: 4px; resize: vertical;"></textarea>
                            </div>
                            <div>
                                <label>用户提示词:</label>
                                <textarea id="user-prompt" rows="5" 
                                    style="width: 100%; padding: 5px; background: #333; border: 1px solid #666; color: #fff; border-radius: 4px; resize: vertical;"></textarea>
                            </div>
                            <div>
                                <label>Temperature:</label>
                                <input type="number" id="temperature" min="0" max="2" step="0.1" value="0.7" 
                                    style="width: 100%; padding: 5px; background: #333; border: 1px solid #666; color: #fff; border-radius: 4px;">
                            </div>
                            <div>
                                <label>Top P:</label>
                                <input type="number" id="top-p" min="0" max="1" step="0.1" value="0.9" 
                                    style="width: 100%; padding: 5px; background: #333; border: 1px solid #666; color: #fff; border-radius: 4px;">
                            </div>
                            <div style="text-align: right; margin-top: 10px;">
                                <button type="button" onclick="this.closest('dialog').close()" 
                                    style="padding: 5px 15px; margin-right: 10px; background: #444; border: 1px solid #666; color: #fff; border-radius: 4px; cursor: pointer;">
                                    取消
                                </button>
                                <button type="submit" 
                                    style="padding: 5px 15px; background: #1e90ff; border: none; color: #fff; border-radius: 4px; cursor: pointer;">
                                    保存
                                </button>
                            </div>
                        </form>
                    `;

                    // 处理表单提交
                    dialog.querySelector("form").onsubmit = async (e) => {
                        e.preventDefault();
                        const name = dialog.querySelector("#preset-name").value;
                        const system_prompt = dialog.querySelector("#system-prompt").value;
                        const user_prompt = dialog.querySelector("#user-prompt").value;
                        const temperature = parseFloat(dialog.querySelector("#temperature").value);
                        const top_p = parseFloat(dialog.querySelector("#top-p").value);

                        if (!name) {
                            alert("请输入预设名称");
                            return;
                        }

                        const success = await PresetService.savePreset({
                            name,
                            system_prompt,
                            user_prompt,
                            temperature,
                            top_p
                        });

                        if (success) {
                            await updatePresets();
                            presetWidget.value = name;
                            dialog.close();
                        } else {
                            alert("保存预设失败");
                        }
                    };

                    document.body.appendChild(dialog);
                    dialog.showModal();
                });

                // 初始加载预设列表
                await updatePresets();
            };
        }
    }
}); 
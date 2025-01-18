import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

// PresetService 定义
const PresetService = {
    async getPresets() {
        try {
            const response = await fetch("/axun/AIAssistant/presets", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (!response.ok) throw new Error("获取预设失败");
            return await response.json();
        } catch (error) {
            console.error("[AIAssistant] 获取预设失败:", error);
            return {};
        }
    },

    async savePreset(type, preset) {
        try {
            const response = await fetch("/axun/AIAssistant/save_preset", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ type, ...preset }),
            });
            if (!response.ok) throw new Error("保存预设失败");
            const result = await response.json();
            return result.status === "success";
        } catch (error) {
            console.error("[AIAssistant] 保存预设失败:", error);
            return false;
        }
    },

    async deletePreset(type, name) {
        try {
            const response = await fetch("/axun/AIAssistant/delete_preset", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ type, name }),
            });
            if (!response.ok) throw new Error("删除预设失败");
            const result = await response.json();
            return result.status === "success";
        } catch (error) {
            console.error("[AIAssistant] 删除预设失败:", error);
            return false;
        }
    },
};

// 更新预设列表函数
async function updatePresets(node) {
    try {
        const presets = await PresetService.getPresets();
        console.log("[AIAssistant] 加载到的预设:", presets);
        
        if (!node || !node.widgets) {
            console.warn("[AIAssistant] 节点或widgets不存在，跳过更新");
            return;
        }

        // 获取所有widgets
        const systemPresetWidget = node.widgets.find((w) => w.name === "system_preset");
        const stylePresetWidget = node.widgets.find((w) => w.name === "style_preset");
        const shotPresetWidget = node.widgets.find((w) => w.name === "shot_preset");
        const characterAPresetWidget = node.widgets.find((w) => w.name === "character_a_preset");
        const characterBPresetWidget = node.widgets.find((w) => w.name === "character_b_preset");
        const characterCPresetWidget = node.widgets.find((w) => w.name === "character_c_preset");
        
        // 更新系统预设
        if (systemPresetWidget) {
            systemPresetWidget.options = systemPresetWidget.options || {};
            systemPresetWidget.options.values = Object.keys(presets.system_presets || {});
            if (!systemPresetWidget.value || !systemPresetWidget.options.values.includes(systemPresetWidget.value)) {
                systemPresetWidget.value = systemPresetWidget.options.values[0] || "null";
            }
        }
        
        // 更新风格预设
        if (stylePresetWidget) {
            stylePresetWidget.options = stylePresetWidget.options || {};
            stylePresetWidget.options.values = Object.keys(presets.style_presets || {});
            if (!stylePresetWidget.value || !stylePresetWidget.options.values.includes(stylePresetWidget.value)) {
                stylePresetWidget.value = stylePresetWidget.options.values[0] || "null";
            }
        }
        
        // 更新镜头预设
        if (shotPresetWidget) {
            shotPresetWidget.options = shotPresetWidget.options || {};
            shotPresetWidget.options.values = Object.keys(presets.shot_presets || {});
            if (!shotPresetWidget.value || !shotPresetWidget.options.values.includes(shotPresetWidget.value)) {
                shotPresetWidget.value = shotPresetWidget.options.values[0] || "null";
            }
        }
        
        // 更新角色预设
        const characterOptions = Object.keys(presets.character_presets || {});
        console.log("[AIAssistant] 角色预设选项:", characterOptions);
        
        for (const widget of [characterAPresetWidget, characterBPresetWidget, characterCPresetWidget]) {
            if (widget) {
                widget.options = widget.options || {};
                widget.options.values = characterOptions;
                if (!widget.value || !characterOptions.includes(widget.value)) {
                    widget.value = characterOptions[0] || "null";
                }
                widget.type = "combo";
                widget.options.editable = false;
            }
        }
        
        app.graph.setDirtyCanvas(true);
    } catch (error) {
        console.error("[AIAssistant] 更新预设失败:", error);
    }
}

// 创建预设对话框
function createPresetDialog(type, title, fields, presets) {
    const dialog = document.createElement("dialog");
    dialog.style.cssText = `
        padding: 20px;
        background: #333;
        color: #fff;
        border: 1px solid #666;
        border-radius: 8px;
        max-width: 600px;
        width: 90%;
    `;
    
    // 创建预设选择下拉框
    const presetOptions = Object.keys(presets).map(name => 
        `<option value="${name}">${name}</option>`
    ).join("");
    
    // 创建表单字段
    const fieldsHtml = `
        <div style="margin-bottom: 15px;">
            <label for="preset_select" style="display: block; margin-bottom: 5px;">选择预设</label>
            <select id="preset_select" style="width: 100%; padding: 5px; background: #444; color: #fff; border: 1px solid #666; border-radius: 4px;">
                <option value="">-- 选择预设 --</option>
                ${presetOptions}
            </select>
        </div>
        ${Object.entries(fields).map(([key, field]) => `
            <div style="margin-bottom: 15px;">
                <label for="${key}" style="display: block; margin-bottom: 5px;">${field.label}</label>
                ${field.type === "textarea" 
                    ? `<textarea id="${key}" rows="${field.rows || 3}" style="width: 100%; padding: 5px; background: #444; color: #fff; border: 1px solid #666; border-radius: 4px;"></textarea>`
                    : `<input type="${field.type}" id="${key}" 
                        ${field.type === "number" ? `step="${field.step || 1}" min="${field.min || 0}" max="${field.max || 100}"` : ""}
                        style="width: 100%; padding: 5px; background: #444; color: #fff; border: 1px solid #666; border-radius: 4px;">`
                }
            </div>
        `).join("")}
    `;
    
    dialog.innerHTML = `
        <h3 style="margin-top: 0;">${title}</h3>
        <form method="dialog" style="display: flex; flex-direction: column; gap: 15px;">
            ${fieldsHtml}
            <div style="text-align: right; margin-top: 10px;">
                <button type="button" onclick="this.closest('dialog').close()" 
                    style="padding: 5px 15px; margin-right: 10px; background: #444; border: 1px solid #666; color: #fff; border-radius: 4px; cursor: pointer;">
                    取消
                </button>
                <button type="button" id="delete_preset_btn"
                    style="padding: 5px 15px; margin-right: 10px; background: #ff4444; border: none; color: #fff; border-radius: 4px; cursor: pointer;">
                    删除
                </button>
                <button type="button" id="load_preset_btn"
                    style="padding: 5px 15px; margin-right: 10px; background: #444; border: 1px solid #666; color: #fff; border-radius: 4px; cursor: pointer;">
                    载入
                </button>
                <button type="submit" 
                    style="padding: 5px 15px; background: #1e90ff; border: none; color: #fff; border-radius: 4px; cursor: pointer;">
                    保存
                </button>
            </div>
        </form>
    `;
    
    document.body.appendChild(dialog);
    dialog.showModal();
    
    // 添加载入预设功能
    const loadPresetBtn = dialog.querySelector("#load_preset_btn");
    const deletePresetBtn = dialog.querySelector("#delete_preset_btn");
    const presetSelect = dialog.querySelector("#preset_select");
    
    // 删除预设功能
    deletePresetBtn.onclick = async () => {
        const selectedPreset = presetSelect.value;
        if (!selectedPreset) {
            alert("请先选择要删除的预设");
            return;
        }

        if (selectedPreset === "null") {
            alert("null预设不能删除");
            return;
        }

        if (type === "system" && selectedPreset === "通用场景") {
            alert("默认场景预设不能删除");
            return;
        }

        if (!confirm(`确定要删除预设"${selectedPreset}"吗？此操作不可恢复。`)) {
            return;
        }

        // 对于角色预设，使用 character 作为类型
        const deleteType = type.startsWith("character") ? "character" : type;
        const success = await PresetService.deletePreset(deleteType, selectedPreset);
        if (success) {
            await updatePresets(this);
            presetSelect.value = "";  // 重置选择框
            // 清空所有输入框
            for (const [key, field] of Object.entries(fields)) {
                const input = dialog.querySelector(`#${key}`);
                if (input) input.value = "";
            }
            alert("删除成功");
            dialog.close();  // 关闭对话框
        } else {
            alert("删除预设失败");
        }
    };
    
    loadPresetBtn.onclick = () => {
        const selectedPreset = presetSelect.value;
        if (!selectedPreset) {
            alert("请先选择一个预设");
            return;
        }
        
        const preset = presets[selectedPreset];
        if (!preset) return;
        
        // 设置预设名称
        const nameInput = dialog.querySelector("#name");
        if (nameInput) nameInput.value = selectedPreset;
        
        // 根据预设类型设置其他字段
        if (type === "system") {
            const systemPromptInput = dialog.querySelector("#system_prompt");
            const temperatureInput = dialog.querySelector("#temperature");
            const topPInput = dialog.querySelector("#top_p");
            
            if (systemPromptInput) systemPromptInput.value = preset.system_prompt || "";
            if (temperatureInput) temperatureInput.value = preset.temperature || 0.7;
            if (topPInput) topPInput.value = preset.top_p || 0.9;
        } else {
            const promptInput = dialog.querySelector("#prompt");
            if (promptInput) promptInput.value = preset.prompt || "";
        }
    };
    
    return dialog;
}

// 注册预设节点
app.registerExtension({
    name: "axun.AIAssistant.preset",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "AIAssistantPreset") {
            const originalNodeCreated = nodeType.prototype.onNodeCreated;
            
            // 添加种子控制处理
            nodeType.prototype.onExecutionStart = function() {
                if (this.widgets) {
                    const seedWidget = this.widgets.find(w => w.name === "seed");
                    const seedModeWidget = this.widgets.find(w => w.name === "seed_mode");
                    
                    if (seedWidget && seedModeWidget) {
                        const currentSeed = parseInt(seedWidget.value);
                        let newSeed = currentSeed;

                        switch(seedModeWidget.value) {
                            case "fixed":
                                // 保持当前种子值不变
                                break;
                            case "increment":
                                newSeed = (currentSeed + 1) >>> 0;  // 确保为正整数
                                break;
                            case "decrement":
                                newSeed = Math.max(0, currentSeed - 1);
                                break;
                            case "randomize":
                                newSeed = Math.floor(Math.random() * 0xffffffffffffffff);
                                break;
                        }

                        if (newSeed !== currentSeed) {
                            seedWidget.value = newSeed;
                            app.graph.setDirtyCanvas(true);
                        }
                    }
                }
            };
            
            nodeType.prototype.onNodeCreated = async function () {
                if (originalNodeCreated) {
                    originalNodeCreated.apply(this, arguments);
                }

                // 添加初始化标记
                if (this._presetsInitialized) {
                    console.debug("[AIAssistant] 预设已初始化，跳过加载");
                    return;
                }
                this._presetsInitialized = true;

                // 获取所有widgets
                const systemPresetWidget = this.widgets.find((w) => w.name === "system_preset");
                const customSystemWidget = this.widgets.find((w) => w.name === "custom_system");
                const stylePresetWidget = this.widgets.find((w) => w.name === "style_preset");
                const shotPresetWidget = this.widgets.find((w) => w.name === "shot_preset");
                const characterAPresetWidget = this.widgets.find((w) => w.name === "character_a_preset");
                const characterBPresetWidget = this.widgets.find((w) => w.name === "character_b_preset");
                const characterCPresetWidget = this.widgets.find((w) => w.name === "character_c_preset");
                const customPromptWidget = this.widgets.find((w) => w.name === "custom_prompt");
                const seedModeWidget = this.widgets.find(w => w.name === "seed_mode");
                const seedWidget = this.widgets.find(w => w.name === "seed");

                // 创建widgets数组
                let widgets = [];

                // 添加系统预设选择器和编辑按钮
                if (systemPresetWidget) {
                    systemPresetWidget.type = "combo";
                    widgets.push(systemPresetWidget);
                    
                    // 添加系统预设编辑按钮
                    const editButton = this.addWidget("button", "编辑场景预设", null, async () => {
                        const presets = await PresetService.getPresets();
                        const dialog = createPresetDialog("system", "编辑场景预设", {
                            name: { label: "预设名称", type: "text" },
                            system_prompt: { label: "系统提示词", type: "textarea", rows: 5 },
                            temperature: { label: "Temperature", type: "number", step: 0.1, precision: 2, min: 0, max: 2 },
                            top_p: { label: "Top P", type: "number", step: 0.1, precision: 2, min: 0, max: 1 }
                        }, presets.system_presets || {});
                        
                        dialog.querySelector("form").onsubmit = async (e) => {
                            e.preventDefault();
                            const formData = {
                                name: dialog.querySelector("#name").value,
                                system_prompt: dialog.querySelector("#system_prompt").value,
                                temperature: parseFloat(dialog.querySelector("#temperature").value),
                                top_p: parseFloat(dialog.querySelector("#top_p").value)
                            };
                            
                            if (!formData.name) {
                                alert("请输入预设名称");
                                return;
                            }
                            
                            const success = await PresetService.savePreset("system", formData);
                            if (success) {
                                await updatePresets(this);
                                systemPresetWidget.value = formData.name;
                                dialog.close();
                            } else {
                                alert("保存预设失败");
                            }
                        };
                    });
                    widgets.push(editButton);
                }

                // 添加风格预设选择器和编辑按钮
                if (stylePresetWidget) {
                    stylePresetWidget.type = "combo";
                    widgets.push(stylePresetWidget);
                    
                    // 添加风格预设编辑按钮
                    const editButton = this.addWidget("button", "编辑风格预设", null, async () => {
                        const presets = await PresetService.getPresets();
                        const dialog = createPresetDialog("style", "编辑风格预设", {
                            name: { label: "风格名称", type: "text" },
                            prompt: { label: "风格提示词", type: "textarea", rows: 5 }
                        }, presets.style_presets || {});
                        
                        dialog.querySelector("form").onsubmit = async (e) => {
                            e.preventDefault();
                            const formData = {
                                name: dialog.querySelector("#name").value,
                                prompt: dialog.querySelector("#prompt").value
                            };
                            
                            if (!formData.name) {
                                alert("请输入预设名称");
                        return;
                    }

                            const success = await PresetService.savePreset("style", formData);
                            if (success) {
                                await updatePresets(this);
                                stylePresetWidget.value = formData.name;
                                dialog.close();
                            } else {
                                alert("保存预设失败");
                            }
                        };
                    });
                    widgets.push(editButton);

                    // 添加自定义风格输入框
                    if (customSystemWidget) {
                        customSystemWidget.type = "textarea";
                        customSystemWidget.options = customSystemWidget.options || {};
                        customSystemWidget.options.multiline = true;
                        widgets.push(customSystemWidget);
                    }
                }

                // 添加镜头预设选择器和编辑按钮
                if (shotPresetWidget) {
                    shotPresetWidget.type = "combo";
                    widgets.push(shotPresetWidget);
                    
                    // 添加镜头预设编辑按钮
                    const editButton = this.addWidget("button", "编辑镜头预设", null, async () => {
                        const presets = await PresetService.getPresets();
                        const dialog = createPresetDialog("shot", "编辑镜头预设", {
                            name: { label: "镜头名称", type: "text" },
                            prompt: { label: "镜头提示词", type: "textarea", rows: 5 }
                        }, presets.shot_presets || {});
                        
                        dialog.querySelector("form").onsubmit = async (e) => {
                            e.preventDefault();
                            const formData = {
                                name: dialog.querySelector("#name").value,
                                prompt: dialog.querySelector("#prompt").value
                            };
                            
                            if (!formData.name) {
                                alert("请输入预设名称");
                        return;
                    }

                            const success = await PresetService.savePreset("shot", formData);
                    if (success) {
                                await updatePresets(this);
                                shotPresetWidget.value = formData.name;
                                dialog.close();
                    } else {
                                alert("保存预设失败");
                            }
                        };
                    });
                    widgets.push(editButton);
                }

                // 添加角色预设选择器
                for (const [widget, prefix] of [
                    [characterAPresetWidget, "A"],
                    [characterBPresetWidget, "B"],
                    [characterCPresetWidget, "C"]
                ]) {
                    if (widget) {
                        widget.type = "combo";
                        widgets.push(widget);
                    }
                }

                // 添加统一的角色预设编辑按钮
                const editCharacterButton = this.addWidget("button", "编辑角色预设", null, async () => {
                    const presets = await PresetService.getPresets();
                    const dialog = createPresetDialog("character", "编辑角色预设", {
                        name: { label: "角色名称", type: "text" },
                        prompt: { label: "角色提示词", type: "textarea", rows: 5 }
                    }, presets.character_presets || {});
                    
                    dialog.querySelector("form").onsubmit = async (e) => {
                        e.preventDefault();
                        const formData = {
                            name: dialog.querySelector("#name").value,
                            prompt: dialog.querySelector("#prompt").value
                        };
                        
                        if (!formData.name) {
                            alert("请输入预设名称");
                            return;
                        }

                        const success = await PresetService.savePreset("character", formData);
                        if (success) {
                            await updatePresets(this);
                            dialog.close();
                        } else {
                            alert("保存预设失败");
                        }
                    };
                });
                widgets.push(editCharacterButton);

                // 添加自定义提示词输入框
                if (customPromptWidget) {
                    customPromptWidget.type = "textarea";
                    customPromptWidget.options = customPromptWidget.options || {};
                    customPromptWidget.options.multiline = true;
                    widgets.push(customPromptWidget);
                }

                // 添加种子控制
                if (seedModeWidget && seedWidget) {
                    // 创建种子模式选择控件
                    seedModeWidget.type = "combo";
                    seedModeWidget.options = seedModeWidget.options || {};
                    seedModeWidget.options.values = ["fixed", "increment", "decrement", "randomize"];
                    seedModeWidget.value = seedModeWidget.options.values[0];
                    widgets.push(seedModeWidget);

                    // 创建种子数值显示控件
                    seedWidget.type = "number";
                    seedWidget.options = seedWidget.options || {};
                    seedWidget.options.min = 0;
                    seedWidget.options.max = Number.MAX_SAFE_INTEGER;
                    seedWidget.options.step = 1;
                    seedWidget.options.precision = 0;
                    widgets.push(seedWidget);
                }

                // 更新节点的widgets
                this.widgets = widgets;

                // 初始加载预设列表
                await updatePresets(this);
            }
        }
    }
}); 
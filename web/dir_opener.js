import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

app.registerExtension({
    name: "Comfy.DirOpener",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === "axun_nodes_DirOpener") {
            // 重写widget创建
            nodeType.prototype.onNodeCreated = function() {
                // 定义目录类型
                const dirTypes = [
                    { name: "character_dir", buttonText: "打开角色目录" },
                    { name: "story_dir", buttonText: "打开故事目录" },
                    { name: "cover_dir", buttonText: "打开封面目录" },
                    { name: "animation_dir", buttonText: "打开动画目录" },
                    { name: "other_dir", buttonText: "打开其他目录" }
                ];

                // 清除默认创建的widgets
                this.widgets = [];
                this.widgets_values = [];
                
                // 按顺序创建输入框和按钮对
                dirTypes.forEach(dirType => {
                    // 创建输入框
                    const inputWidget = this.addWidget(
                        "string",
                        dirType.name,
                        "",
                        (value) => {
                            this.widgets_values[dirType.name] = value;
                        },
                        {
                            multiline: false
                        }
                    );
                    
                    // 创建对应的按钮
                    const buttonWidget = this.addWidget("button", dirType.buttonText, null, async () => {
                        const directory = inputWidget.value;
                        if (!directory) {
                            alert("请先输入目录路径");
                            return;
                        }
                        
                        try {
                            const encodedPath = encodeURIComponent(directory);
                            const response = await api.fetchApi(
                                `/axun-dir/open-directory?directory=${encodedPath}`
                            );
                            
                            if (!response.ok) {
                                const error = await response.text();
                                alert(`打开目录失败: ${error}`);
                            }
                        } catch (error) {
                            alert(`打开目录失败: ${error.message}`);
                        }
                    });
                    buttonWidget.serialize = false;
                });
            };
        }
    }
}); 
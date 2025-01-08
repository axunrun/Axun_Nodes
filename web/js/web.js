import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';
import "./translator.js";

/**
 * 全局状态管理
 */
const state = {
    hasTk: false,
    isUpdating: false
};

/**
 * API请求工具类
 */
class ApiService {
    /**
     * 带重试的API请求
     */
    static async fetchWithRetry(url, options = {}, retries = 3) {
        for (let i = 0; i < retries; i++) {
            try {
                const response = await api.fetchApi(url, options);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return await response.json();
            } catch (error) {
                if (i === retries - 1) throw error;
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            }
        }
    }

    /**
     * 选择目录
     */
    static async getDirectory(nodeId) {
        try {
            const response = await api.fetchApi(`/axun-dir/select-directory?id=${nodeId}`);
            const data = await response.json();
            return data.folder;
        } catch (error) {
            console.error('目录选择失败:', error);
            return null;
        }
    }

    /**
     * 获取循环索引
     */
    static async getLoopIndex(node_id) {
        try {
            const data = await this.fetchWithRetry(`/axun-dir/loop-index?id=${node_id}`);
            return Math.floor(parseInt(data.loop_index) || 0);
        } catch (error) {
            console.error('获取循环索引失败:', error);
            return 0;
        }
    }

    /**
     * 设置循环索引
     */
    static async setLoopIndex(node_id, loop_index) {
        try {
            const data = await this.fetchWithRetry(
                `/axun-dir/set-loop-index?id=${node_id}&index=${Math.floor(loop_index)}`
            );
            return data.success;
        } catch (error) {
            console.error('设置循环索引失败:', error);
            return false;
        }
    }
}

// 注册目录选择器扩展
app.registerExtension({
    name: "AxunNodes.DirPicker",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === 'axun_nodes_DirPicker') {
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const node = this;
                
                // 获取目录输入控件
                const directoryWidget = node.widgets.find(w => w.name === "directory");
                if (!directoryWidget) return;
                
                // 添加选择按钮
                node.addWidget("button", "选择目录", null, () => {
                    ApiService.getDirectory(node.id).then(folder => {
                        if (folder) {
                            directoryWidget.value = folder;
                            node.onWidgetChanged(directoryWidget);
                        }
                    });
                });
            };
        }
    }
});

// 注册路径处理器扩展
app.registerExtension({
    name: "AxunNodes.Path",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === 'axun_nodes_PathProcessor') {
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const node = this;
                
                // 获取loop_index控件
                const loopIndexWidget = node.widgets.find(w => w.name === 'loop_index');
                if (loopIndexWidget) {
                    // 从后端获取初始索引
                    ApiService.getLoopIndex(node.id).then(loop_index => {
                        loopIndexWidget.value = loop_index;
                        node.onWidgetChanged(loopIndexWidget);
                    });

                    // 添加afterQueued回调
                    loopIndexWidget.afterQueued = () => {
                        // 不再自动递增，让后端处理
                        node.onWidgetChanged(loopIndexWidget);
                    }

                    // 添加callback同步到后端
                    loopIndexWidget.callback = async function() {
                        await ApiService.setLoopIndex(node.id, loopIndexWidget.value);
                        node.onWidgetChanged(loopIndexWidget);
                    }

                    // 监听executed事件
                    api.addEventListener('executed', async () => {
                        const currentIndex = await ApiService.getLoopIndex(node.id);
                        if (currentIndex !== loopIndexWidget.value) {
                            loopIndexWidget.value = currentIndex;
                            node.onWidgetChanged(loopIndexWidget);
                        }
                    });

                    // 监听queue事件
                    api.addEventListener('queue', () => {
                        node.onWidgetChanged(loopIndexWidget);
                    });
                }
            };
        }
    }
});

// 注册队列触发器扩展
app.registerExtension({
    name: "AxunNodes.QueueTrigger",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === 'axun_nodes_QueueTrigger') {
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const node = this;
                
                // 获取count控件
                const countWidget = node.widgets.find(w => w.name === 'count');
                if (countWidget) {
                    // 监听executed事件
                    api.addEventListener('executed', () => {
                        node.onWidgetChanged(countWidget);
                    });

                    // 监听queue事件
                    api.addEventListener('queue', () => {
                        node.onWidgetChanged(countWidget);
                    });
                }
            };
        }
    }
}); 
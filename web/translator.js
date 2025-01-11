import { api } from '../../../scripts/api.js';
import { app } from '../../../scripts/app.js';

/**
 * 全局状态管理
 */
const state = {
    hasTk: false,    // 标记是否有翻译API的token/密钥
    isUpdating: false // 标记是否正在进行更新操作
};

async function translateText(text) {
    try {
        console.log("[Translator] 发送翻译请求:", text);
        const response = await fetch("/translator/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        if (result.error) {
            throw new Error(result.error);
        }
        console.log("[Translator] 翻译结果:", result.translated);
        return result.translated;
    } catch (error) {
        console.error("[Translator] 翻译失败:", error);
        return null;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function setupTranslator() {
    console.log("[Translator] 开始设置翻译器...");
    
    // 立即处理已存在的文本框
    document.querySelectorAll('.comfy-multiline-input, .lg-input').forEach(textarea => {
        console.log("[Translator] 发现现有文本框，设置事件");
        setupTextAreaEvents(textarea);
    });
    
    // 监听新添加的文本框
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.classList && 
                    (node.classList.contains("comfy-multiline-input") || 
                     node.classList.contains("lg-input"))) {
                    console.log("[Translator] 发现新文本框，设置事件");
                    setupTextAreaEvents(node);
                }
            });
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    console.log("[Translator] 观察器已启动");
}

function setupTextAreaEvents(textarea) {
    const handleTranslation = async () => {
        const text = textarea.value;
        if (!text) return;
        
        console.log("[Translator] 检测到双击，开始翻译");
        const translated = await translateText(text);
        if (translated) {
            textarea.value = translated;
            // 触发input事件，确保UI更新
            const event = new Event('input', { bubbles: true });
            textarea.dispatchEvent(event);
            // 同时触发change事件
            const changeEvent = new Event('change', { bubbles: true });
            textarea.dispatchEvent(changeEvent);
        }
    };

    const debouncedTranslation = debounce(handleTranslation, 300);
    
    textarea.addEventListener("dblclick", (e) => {
        console.log("[Translator] 捕获到双击事件");
        e.preventDefault();
        debouncedTranslation();
    });
}

// 直接初始化
setupTranslator(); 
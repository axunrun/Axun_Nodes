import { app } from '../../../scripts/app.js';

async function translateText(text) {
    try {
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
        return result.translated;
    } catch (error) {
        console.error("Translation failed:", error);
        return null;
    }
}

// 防抖函数
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

// 监听文本框双击事件
function setupTranslator() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.classList && 
                    (node.classList.contains("comfy-multiline-input") || 
                     node.classList.contains("lg-input"))) {
                    setupTextAreaEvents(node);
                }
            });
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
}

// 设置文本框事件
function setupTextAreaEvents(textarea) {
    const handleTranslation = async () => {
        const text = textarea.value;
        if (!text) return;
        
        const translated = await translateText(text);
        if (translated) {
            textarea.value = translated;
            // 触发ComfyUI的更新
            textarea.dispatchEvent(new Event("input"));
        }
    };

    // 使用防抖处理双击事件
    const debouncedTranslation = debounce(handleTranslation, 300);
    
    textarea.addEventListener("dblclick", (e) => {
        e.preventDefault();
        debouncedTranslation();
    });
}

// 初始化
setupTranslator(); 
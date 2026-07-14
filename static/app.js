/**
 * 电商客服 AI Agent — 前端交互逻辑
 */

const messagesEl = document.getElementById("messages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

let isStreaming = false;

// ---------- 发送消息 ----------

async function sendMessage() {
    if (isStreaming) return;
    const text = userInput.value.trim();
    if (!text) return;

    isStreaming = true;
    sendBtn.disabled = true;

    // 添加用户消息
    appendMessage("user", text);
    userInput.value = "";
    userInput.style.height = "auto";

    // 添加助手占位
    const assistantMsg = appendMessage("assistant", "");
    // 显示输入指示器
    const typing = addTyping();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });

        // 移除输入指示器
        typing.remove();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullText = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const data = JSON.parse(line.slice(6));
                    if (data === "[DONE]") continue;
                    fullText += data;
                    assistantMsg.textContent = fullText;
                    scrollToBottom();
                }
            }
        }

        // 如果没内容，显示默认
        if (!fullText.trim()) {
            assistantMsg.textContent = "收到，让我想想...";
        }
    } catch (err) {
        typing.remove();
        assistantMsg.textContent = "抱歉，连接出现了问题：" + err.message;
    } finally {
        isStreaming = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// ---------- 重置对话 ----------

async function resetChat() {
    if (isStreaming) return;
    try {
        await fetch("/api/reset", { method: "POST" });
        messagesEl.innerHTML = "";
        // 重新显示欢迎消息
        appendMessage("assistant",
            "您好！我是您的专属客服助手 <strong>小智</strong> 👋<br><br>" +
            "我可以帮您：<br>" +
            "📦 <strong>查询订单</strong> — 告诉我订单号或手机号<br>" +
            "📋 <strong>解答常见问题</strong> — 退货、发货、尺码等<br>" +
            "🔄 <strong>处理退换货</strong> — 帮您创建退货申请<br>" +
            "🛍️ <strong>推荐商品</strong> — 告诉我您的需求<br><br>" +
            "请问有什么可以帮您的？"
        );
    } catch (err) {
        console.error("重置失败:", err);
    }
}

// ---------- 辅助函数 ----------

function appendMessage(role, content) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.innerHTML = content;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
}

function addTyping() {
    const div = document.createElement("div");
    div.className = "typing-indicator";
    div.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// 自动调整 textarea 高度
userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 100) + "px";
});

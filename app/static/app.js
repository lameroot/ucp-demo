const chatWindow = document.getElementById("chat-window");
const sendButton = document.getElementById("send-message");
const messageInput = document.getElementById("chat-message");
const merchantSelect = document.getElementById("merchant-select");
const payOrderButton = document.getElementById("pay-order");
const orderStatus = document.getElementById("order-status");
const loadCatalogButton = document.getElementById("load-catalog");

let currentOrderId = null;

function appendMessage(text, sender = "assistant") {
    const wrapper = document.createElement("div");
    wrapper.className = `chat-message ${sender}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerText = text;
    wrapper.appendChild(bubble);
    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(message) {
    const merchantId = merchantSelect.value;
    appendMessage(message, "user");
    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ merchant_id: parseInt(merchantId, 10), message }),
    });
    const data = await response.json();
    appendMessage(data.reply || "Нет ответа", "assistant");
    if (data.order_id) {
        currentOrderId = data.order_id;
        payOrderButton.disabled = false;
        orderStatus.innerText = `Создан заказ #${data.order_id}`;
    }
}

sendButton?.addEventListener("click", () => {
    const message = messageInput.value.trim();
    if (!message) return;
    messageInput.value = "";
    sendMessage(message);
});

messageInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendButton.click();
    }
});

payOrderButton?.addEventListener("click", async () => {
    if (!currentOrderId) return;
    payOrderButton.disabled = true;
    orderStatus.innerText = "Оплата...";
    const response = await fetch(`/api/orders/${currentOrderId}/purchase`, {
        method: "POST",
    });
    const data = await response.json();
    orderStatus.innerText = `Статус: ${data.status}`;
    appendMessage(`Платеж ${data.status}.`, "assistant");
});

loadCatalogButton?.addEventListener("click", () => {
    sendMessage("Покажи каталог товаров");
});

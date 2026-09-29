async function generate(action) {
    const text = document.getElementById("text").value;
    const output = document.getElementById("output");
    const originalText = document.getElementById("originalText");
    const copyButton = document.getElementById("copyButton");

    copyButton.style.display = "none";

    if (!text.trim()) {
        output.textContent = "Введите текст.";
        originalText.textContent = "Здесь появится исходный текст...";
        return;
    }

    originalText.textContent = text;

    output.innerHTML = `
        <div class="loader">
            <div class="spinner"></div>
            <span>Генерирую...</span>
        </div>
    `;

    try {
        const response = await fetch("http://127.0.0.1:8000/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: text,
                action: action
            })
        });

        const data = await response.json();

        if (data.error) {
            output.textContent = "Ошибка: " + data.error;
            return;
        }

        output.textContent = data.result;
        copyButton.style.display = "block";

    } catch (error) {
        output.textContent = "Не удалось подключиться к серверу.";
        console.error(error);
    }
}
async function copyResult() {
    const output = document.getElementById("output");
    const copyButton = document.getElementById("copyButton");

    await navigator.clipboard.writeText(output.textContent);

    copyButton.textContent = "✓ Скопировано";

    setTimeout(() => {
        copyButton.textContent = "📋 Копировать";
    }, 1500);
}
function clearAll() {
    const text = document.getElementById("text");
    const output = document.getElementById("output");
    const originalText = document.getElementById("originalText");
    const copyButton = document.getElementById("copyButton");

    text.value = "";

    originalText.textContent = "Здесь появится исходный текст...";
    output.textContent = "Здесь появится результат...";

    copyButton.style.display = "none";
}
async function toggleHistory() {
    const panel = document.getElementById("historyPanel");

    panel.classList.toggle("open");

    if (panel.classList.contains("open")) {
        await loadHistory();
    }
}
async function loadHistory() {
    const historyList = document.getElementById("historyList");

    historyList.innerHTML = "Загрузка...";

    try {
        const response = await fetch("http://127.0.0.1:8000/history");
        const history = await response.json();

        if (history.length === 0) {
            historyList.innerHTML = "История пока пуста.";
            return;
        }

        historyList.innerHTML = "";

        history.forEach(item => {
            const historyItem = document.createElement("div");
            historyItem.className = "historyItem";

            const header = document.createElement("div");
            header.className = "historyItemHeader";

            header.innerHTML = `
                <strong>${getActionName(item.action)}</strong>
                <small>${formatDate(item.created_at)}</small>
            `;

            const preview = document.createElement("p");
            preview.textContent = item.input_text.substring(0, 80) + "...";

            const details = document.createElement("div");
            details.className = "historyDetails";

            const inputTitle = document.createElement("strong");
            inputTitle.textContent = "Исходный текст:";

            const inputText = document.createElement("div");
            inputText.className = "historyText";
            inputText.textContent = item.input_text;

            const resultTitle = document.createElement("strong");
            resultTitle.textContent = "Результат:";

            const resultText = document.createElement("div");
            resultText.className = "historyText";
            resultText.textContent = item.result;

            const closeButton = document.createElement("button");
            closeButton.textContent = "Свернуть";
            closeButton.className = "collapseButton";

            closeButton.addEventListener("click", (event) => {
                event.stopPropagation();
                historyItem.classList.remove("expanded");
            });

            details.appendChild(inputTitle);
            details.appendChild(inputText);
            details.appendChild(resultTitle);
            details.appendChild(resultText);
            details.appendChild(closeButton);

            historyItem.appendChild(header);
            historyItem.appendChild(preview);
            historyItem.appendChild(details);

            historyItem.addEventListener("click", () => {
                historyItem.classList.toggle("expanded");
            });

            historyList.appendChild(historyItem);
        });

    } catch (error) {
        console.error(error);
        historyList.innerHTML = "Не удалось загрузить историю.";
    }
}

function getActionName(action) {
    const names = {
        summarize: "Сокращение",
        improve: "Улучшение",
        translate: "Перевод",
        telegram: "Telegram",
        headlines: "Заголовки",
        keywords: "Ключевые слова",
        seo: "SEO-анализ"
    };

    return names[action] || action;
}


function formatDate(date) {
    return new Date(date).toLocaleString("ru-RU");
}
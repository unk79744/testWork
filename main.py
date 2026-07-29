import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="Booking AI Assistant")

# 👇👇👇 ВСТАВЬ СВОЙ КЛЮЧ ОТ GROQ ПРЯМО В ЭТИ КАВЫЧКИ 👇👇👇
API_KEY = os.getenv("LLM_API_KEY", "")

class ChatRequest(BaseModel):
    passport_received: bool
    user_message: str

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Помощник Бронирования</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #f4f6f8; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 100%; max-width: 500px; }
        h2 { margin-top: 0; color: #1a1a1a; }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 6px; font-weight: 600; color: #4a5568; }
        select, textarea, button { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e0; box-sizing: border-box; font-size: 14px; }
        textarea { height: 80px; resize: vertical; }
        button { background: #0066ff; color: white; border: none; font-weight: 600; cursor: pointer; margin-top: 8px; }
        button:disabled { background: #a0aec0; }
        .response-box { margin-top: 20px; padding: 12px; background: #f7fafc; border-left: 4px solid #0066ff; border-radius: 4px; display: none; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h2>AI Бронирование</h2>
        
        <div class="form-group">
            <label>Статус паспорта:</label>
            <select id="passportStatus">
                <option value="false">Паспорт НЕ получен</option>
                <option value="true">Паспорт получен</option>
            </select>
        </div>

        <div class="form-group">
            <label>Сообщение гостя:</label>
            <textarea id="userMessage" placeholder="Введите сообщение...">Как мне заселиться?</textarea>
        </div>

        <button id="sendBtn" onclick="sendMessage()">Получить ответ ИИ</button>
        <div id="responseBox" class="response-box"></div>
    </div>

    <script>
        async function sendMessage() {
            const status = document.getElementById('passportStatus').value === 'true';
            const message = document.getElementById('userMessage').value;
            const btn = document.getElementById('sendBtn');
            const resBox = document.getElementById('responseBox');

            if (!message.trim()) return;

            btn.disabled = true;
            btn.innerText = "ИИ думает...";
            resBox.style.display = "none";

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ passport_received: status, user_message: message })
                });

                const data = await response.json();
                
                if (response.ok && data.reply) {
                    resBox.innerText = data.reply;
                    resBox.style.display = "block";
                } else {
                    // Теперь мы увидим НАСТОЯЩУЮ ошибку от Groq или Python
                    alert("Ошибка сервера:\\n" + (data.detail || "Неизвестная ошибка"));
                }
            } catch (err) {
                alert("Сетевая ошибка! Проверь, не отвалился ли сервер.");
            } finally {
                btn.disabled = false;
                btn.innerText = "Получить ответ ИИ";
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTML_CONTENT

@app.post("/api/chat")
def chat_with_ai(data: ChatRequest):
    if not API_KEY or "ТУТ_ТВОЙ_РЕАЛЬНЫЙ_КЛЮЧ" in API_KEY:
        raise HTTPException(status_code=400, detail="Ключ не установлен в коде!")

    # Обновленный промпт — даем роль живого человека
    system_prompt = f"""
Ты — вежливый, отзывчивый и грамотный менеджер службы поддержки сервиса бронирования. 
Твоя задача — естественно пообщаться с гостем, ответить на его вопрос и подсказать следующие шаги, учитывая статус его документов.

Текущий статус документов гостя:
- Паспорт получен: {"ДА" if data.passport_received else "НЕТ"}

ПРАВИЛА ОТВЕТА:
1. Если статус "Паспорт получен: НЕТ":
   - Ответь на конкретное сообщение гостя своими словами (вежливо и по-человечески).
   - Объясни, что для продолжения бронирования или заселения обязательно нужно предоставить паспорт.
   - Вставь в текст ссылку для загрузки: https://example.com/passport

2. Если статус "Паспорт получен: ДА":
   - Подтверди, что паспорт уже успешно принят.
   - Объясни, что следующим и главным этапом будет оплата залога.

Пиши грамотным русским языком, как реальный менеджер в чате. Не используй заученные клише.
"""

    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.user_message}
            ],
            temperature=0.5  # Чуть подняли для более живой речи
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
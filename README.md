# UCP Demo

Демо показывает работу UCP протокола с несколькими мерчантами и чат-клиентом.

## Возможности
- Управление мерчантами и товарами через простой веб-интерфейс.
- A2A эндпоинты для мерчантов (`/a2a/{merchant_id}/...`).
- Чат-клиент для общения с агентами и оформления заказа.
- Интеграция с mock-сервером `ucp-client` через переменную `UCP_MOCK_URL`.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Откройте:
- `http://localhost:8000/merchants` — настройка мерчантов.
- `http://localhost:8000/chat` — чат-клиент.

## Настройки

- `OPENAI_API_KEY` — ключ для LLM.
- `OPENAI_MODEL` — модель, по умолчанию `gpt-4o-mini`.
- `UCP_MOCK_URL` — адрес mock-сервера UCP (например, `http://localhost:8080`).


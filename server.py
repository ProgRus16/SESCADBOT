from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS (если нужно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замени на нужные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock база данных
businesses_db: Dict[str, Dict] = {}  # {user_id: {business_name: business_data}}
activation_keys_db = {"TESTKEY123": True}  # ключ: активен ли
users_db = set()
advertisements = []

# Модели
class BusinessRegistration(BaseModel):
    user_id: str
    business_name: str
    description: str
    members: List[str]
    contacts: str

class AdvertiseRequest(BaseModel):
    user_id: str
    business_name: str
    activation_key: str
    advertisement_text: str

class SupportMessage(BaseModel):
    user_id: str
    message: str


@app.post("/register_business")
def register_business(data: BusinessRegistration):
    # Проверка ключа (в будущем можно сделать проверку по ключу в БД)
    if data.activation_key not in activation_keys_db or not activation_keys_db[data.activation_key]:
        raise HTTPException(status_code=400, detail="Неверный или неактивный ключ активации")

    # Проверка, существует ли уже бизнес с таким именем у этого пользователя
    if data.user_id in businesses_db and data.business_name in businesses_db[data.user_id]:
        raise HTTPException(status_code=400, detail="Бизнес с таким именем уже зарегистрирован")

    # Регистрация
    if data.user_id not in businesses_db:
        businesses_db[data.user_id] = {}

    businesses_db[data.user_id][data.business_name] = {
        "name": data.business_name,
        "description": data.description,
        "members": data.members,
        "contacts": data.contacts,
        "priority": 0
    }
    users_db.add(data.user_id)

    print(f"✅ Зарегистрирован бизнес: {data.business_name} (пользователь: {data.user_id})")
    return {"status": "success"}


@app.post("/advertise")
def advertise_business(data: AdvertiseRequest):
    # Проверка ключа
    if data.activation_key not in activation_keys_db or not activation_keys_db[data.activation_key]:
        raise HTTPException(status_code=400, detail="Неверный или неактивный ключ активации")

    # Проверка, существует ли бизнес
    if data.user_id not in businesses_db or data.business_name not in businesses_db[data.user_id]:
        raise HTTPException(status_code=404, detail="Бизнес не найден")

    # Увеличиваем приоритет
    businesses_db[data.user_id][data.business_name]["priority"] += 1

    # Сохраняем рекламу (можно использовать для рассылки)
    advertisements.append({
        "business_name": data.business_name,
        "text": data.advertisement_text,
        "user_id": data.user_id
    })

    print(f"📢 Рекламируется: {data.business_name} | Приоритет: {businesses_db[data.user_id][data.business_name]['priority']}")
    return {"status": "Реклама разослана"}


@app.post("/send_support_message")
def send_support_message(data: SupportMessage):
    print(f"📩 Сообщение в поддержку от {data.user_id}: {data.message}")
    return {"status": "Сообщение отправлено разработчику"}


@app.get("/get_businesses")
def get_businesses():
    all_businesses = []
    for user_businesses in businesses_db.values():
        for business in user_businesses.values():
            all_businesses.append({
                "name": business["name"],
                "description": business["description"],
                "members": business["members"],
                "contacts": business["contacts"],
                "priority": business["priority"]
            })

    # Сортировка по приоритету (высокий приоритет — выше)
    all_businesses.sort(key=lambda x: x["priority"], reverse=True)
    return {"businesses": all_businesses}


# Опционально: эндпоинт для просмотра всех бизнесов (для отладки)
@app.get("/debug/businesses")
def debug_businesses():
    return businesses_db


if __name__ == "__main__":
    print("🚀 Сервер запущен на http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import uvicorn

app = FastAPI()

# Mock база данных
businesses_db: Dict[str, Dict] = {}  # {user_id: {business_name: business_data}}
activation_keys_db = {"TESTKEY123": True}  # В реальности должна быть БД ключей
users_db = set()  # Множество user_id
advertisements = []  # Список рекламных сообщений

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
    if data.user_id not in businesses_db:
        businesses_db[data.user_id] = {}
    businesses_db[data.user_id][data.business_name] = {
        "description": data.description,
        "members": data.members,
        "contacts": data.contacts,
        "priority": 0  # Приоритет по умолчанию
    }
    users_db.add(data.user_id)
    return {"status": "success"}

@app.post("/advertise")
def advertise_business(data: AdvertiseRequest):
    if data.activation_key not in activation_keys_db:
        raise HTTPException(status_code=400, detail="Неверный ключ активации")
    if data.user_id not in businesses_db or data.business_name not in businesses_db[data.user_id]:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    advertisements.append({
        "business_name": data.business_name,
        "text": data.advertisement_text
    })
    # Увеличиваем приоритет бизнеса
    businesses_db[data.user_id][data.business_name]["priority"] += 1
    return {"status": "Реклама разослана"}

@app.post("/send_support_message")
def send_support_message(data: SupportMessage):
    # В реальности можно отправить сообщение разработчику (например, в Telegram или email)
    print(f"Сообщение в поддержку от {data.user_id}: {data.message}")
    return {"status": "Сообщение отправлено разработчику"}

@app.get("/get_businesses")
def get_businesses():
    # Сортируем бизнесы по приоритету (чем выше приоритет, тем выше в списке)
    all_businesses = []
    for user_businesses in businesses_db.values():
        for name, data in user_businesses.items():
            all_businesses.append({
                "name": name,
                "priority": data["priority"]
            })
    # Сортируем по приоритету (по убыванию)
    all_businesses.sort(key=lambda x: x["priority"], reverse=True)
    return {"businesses": all_businesses}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
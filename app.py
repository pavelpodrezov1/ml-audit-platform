from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import json
import numpy as np
from typing import List
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="Titanic ML Model API",
    description="API для предсказания выживаемости на Titanic",
    version="1.0.0"
)

# Загружаем модель и scaler при запуске
model = None
scaler = None
model_info = None

@app.on_event("startup")
async def load_model():
    """Загружаем модель при запуске приложения"""
    global model, scaler, model_info
    try:
        model = joblib.load('models/titanic_model.pkl')
        scaler = joblib.load('models/titanic_scaler.pkl')
        with open('models/model_info.json', 'r') as f:
            model_info = json.load(f)
        logger.info("✓ Модель загружена успешно")
    except Exception as e:
        logger.error(f"✗ Ошибка при загрузке модели: {e}")
        raise

# Определяем схему для входных данных
class PassengerData(BaseModel):
    pclass: int      # 1, 2 или 3
    sex: int         # 0 для male, 1 для female
    age: float
    sibsp: int       # количество братьев/сестер
    parch: int       # количество родителей/детей
    fare: float
    embarked: int    # 0 для S, 1 для C, 2 для Q

class PredictionResponse(BaseModel):
    prediction: int      # 0 = не выжил, 1 = выжил
    probability: float
    message: str

# Эндпоинты API

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Titanic ML Model API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_info": model_info
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(passenger: PassengerData):
    """
    Предсказывает выживаемость пассажира
    
    Пример использования:
    ```json
    {
        "pclass": 1,
        "sex": 1,
        "age": 30,
        "sibsp": 0,
        "parch": 0,
        "fare": 100,
        "embarked": 0
    }
    ```
    
    Параметры:
    - pclass (int): Класс каюты (1, 2 или 3)
    - sex (int): Пол (0 = мужской, 1 = женский)
    - age (float): Возраст в годах
    - sibsp (int): Количество братьев/сестер на борту
    - parch (int): Количество родителей/детей на борту
    - fare (float): Стоимость билета
    - embarked (int): Порт посадки (0 = Southampton, 1 = Cherbourg, 2 = Queenstown)
    
    Возвращает:
    - prediction (int): 0 = не выжил, 1 = выжил
    - probability (float): Вероятность выживания (от 0 до 1)
    - message (str): Человеко-читаемое сообщение
    """
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Подготавливаем данные в правильном формате (1, 7)
        X = np.array([[
            passenger.pclass,
            passenger.sex,
            passenger.age,
            passenger.sibsp,
            passenger.parch,
            passenger.fare,
            passenger.embarked
        ]])
        
        # Масштабируем данные
        X_scaled = scaler.transform(X)
        
        # Получаем предсказание
        prediction = int(model.predict(X_scaled))
        
        # Получаем вероятности
        # model.predict_proba() возвращает массив формата (n_samples, n_classes)
        # В нашем случае (1, 2) - вероятности для классов [не выжил, выжил]
        probabilities = model.predict_proba(X_scaled)
        survival_probability = float(probabilities[0, 1])  # Вероятность класса "выжил"
        
        # Формируем сообщение
        message = f"Пассажир {'выжил' if prediction == 1 else 'не выжил'} (уверенность: {survival_probability:.2%})"
        
        logger.info(f"Prediction made: {message}")
        
        return PredictionResponse(
            prediction=prediction,
            probability=survival_probability,
            message=message
        )
    
    except Exception as e:
        logger.error(f"Ошибка при предсказании: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/model-info")
async def get_model_info():
    """Возвращает информацию о модели"""
    if model_info is None:
        raise HTTPException(status_code=503, detail="Model info not available")
    return model_info

@app.post("/batch-predict")
async def batch_predict(passengers: List[PassengerData]):
    """
    Пакетное предсказание для нескольких пассажиров
    
    Пример использования:
    ```json
    [
        {"pclass":1,"sex":1,"age":30,"sibsp":0,"parch":0,"fare":100,"embarked":0},
        {"pclass":3,"sex":0,"age":25,"sibsp":1,"parch":0,"fare":50,"embarked":2}
    ]
    ```
    """
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        results = []
        
        for passenger in passengers:
            X = np.array([[
                passenger.pclass,
                passenger.sex,
                passenger.age,
                passenger.sibsp,
                passenger.parch,
                passenger.fare,
                passenger.embarked
            ]])
            
            X_scaled = scaler.transform(X)
            prediction = int(model.predict(X_scaled))
            probabilities = model.predict_proba(X_scaled)
            survival_probability = float(probabilities[0, 1])
            
            results.append({
                "prediction": prediction,
                "probability": survival_probability,
                "survived": bool(prediction)
            })
        
        return {
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Ошибка при пакетном предсказании: {e}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


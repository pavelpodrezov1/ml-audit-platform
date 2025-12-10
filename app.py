from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(
    title="ML Audit Platform",
    description="Titanic Survival Prediction API",
    version="1.0.0"
)

MODEL_PATH = "models/titanic_model.pkl"

try:
    model = joblib.load(MODEL_PATH)
    print(f"✓ Model loaded from {MODEL_PATH}")
except FileNotFoundError:
    print(f"✗ Model not found at {MODEL_PATH}")
    model = None
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None


class PassengerData(BaseModel):
    pclass: int
    sex: int
    age: float
    sibsp: int
    parch: int
    fare: float
    embarked: int


@app.get("/health")
def health_check():
    """Health check endpoint"""
    model_status = "loaded" if model is not None else "not_loaded"
    return {
        "status": "healthy",
        "model": model_status,
        "service": "ml-audit-platform"
    }


@app.post("/predict")
def predict(passenger: PassengerData):
    """Predict Titanic passenger survival"""
    if model is None:
        return {
            "error": "Model not loaded",
            "message": f"Model file not found at {MODEL_PATH}"
        }
    
    try:
        features = np.array([[
            passenger.pclass,
            passenger.sex,
            passenger.age,
            passenger.sibsp,
            passenger.parch,
            passenger.fare,
            passenger.embarked
        ]])
        
        prediction = model.predict(features)[0]
        
        try:
            probabilities = model.predict_proba(features)[0]
            probability = float(probabilities[1])
        except:
            probability = float(prediction)
        
        return {
            "prediction": int(prediction),
            "probability": probability,
            "prediction_text": "Survived" if prediction == 1 else "Did not survive",
            "input": passenger.dict()
        }
    
    except Exception as e:
        return {
            "error": "Prediction failed",
            "message": str(e)
        }


@app.get("/info")
def info():
    """API info"""
    return {
        "name": "ML Audit Platform",
        "version": "1.0.0",
        "model_status": "loaded" if model is not None else "not_loaded",
        "endpoints": {
            "health": "GET /health",
            "predict": "POST /predict",
            "info": "GET /info",
            "docs": "GET /docs"
        }
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to ML Audit Platform",
        "docs": "/docs"
    }

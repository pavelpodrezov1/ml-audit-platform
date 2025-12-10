import joblib
import pickle
import json
from train_model import train_titanic_model

def save_model_and_artifacts():
    """Сохраняет модель, scaler и метаданные"""
    
    print("Обучаем и сохраняем модель...")
    model, scaler, metrics = train_titanic_model()
    
    # Сохраняем модель (joblib рекомендуется для sklearn)
    print("\nСохраняем модель...")
    joblib.dump(model, 'models/titanic_model.pkl')
    print("✓ Модель сохранена в models/titanic_model.pkl")
    
    # Сохраняем scaler
    joblib.dump(scaler, 'models/titanic_scaler.pkl')
    print("✓ Scaler сохранен в models/titanic_scaler.pkl")
    
    # Сохраняем метрики в JSON
    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print("✓ Метрики сохранены в models/metrics.json")
    
    # Сохраняем информацию о модели
    model_info = {
        'model_type': 'RandomForestClassifier',
        'n_features': 7,
        'features': ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked'],
        'version': '1.0',
        'metrics': metrics
    }
    
    with open('models/model_info.json', 'w') as f:
        json.dump(model_info, f, indent=2)
    print("✓ Информация о модели сохранена в models/model_info.json")

if __name__ == '__main__':
    import os
    os.makedirs('models', exist_ok=True)
    save_model_and_artifacts()


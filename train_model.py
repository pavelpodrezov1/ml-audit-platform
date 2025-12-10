import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings

warnings.filterwarnings('ignore')

def preprocess_data(df):
    """Предобработка данных Titanic"""
    
    # Копируем датафрейм
    df = df.copy()
    
    # Обработка пропущенных значений
    df['Age'].fillna(df['Age'].median(), inplace=True)
    df['Embarked'].fillna(df['Embarked'].mode(), inplace=True)
    
    # Кодирование категориальных переменных
    df['Sex'] = df['Sex'].map({'male': 0, 'female': 1})
    df['Embarked'] = df['Embarked'].map({'S': 0, 'C': 1, 'Q': 2})
    
    # Выбираем признаки
    features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked']
    X = df[features].fillna(0)
    
    return X

def train_titanic_model():
    """Обучает RandomForest модель на данных Titanic"""
    
    print("=" * 60)
    print("ОБУЧЕНИЕ ML-МОДЕЛИ TITANIC")
    print("=" * 60)
    
    # Загружаем данные
    print("\n1. Загружаем данные...")
    df_train = pd.read_csv('data/train.csv')
    print(f"   ✓ Загружено {len(df_train)} образцов")
    
    # Предобработка
    print("\n2. Предобработка данных...")
    X = preprocess_data(df_train)
    y = df_train['Survived']
    print(f"   ✓ Признаки: {X.shape} колонок")
    print(f"   ✓ Распределение классов: {y.value_counts().to_dict()}")
    
    # Разделяем данные
    print("\n3. Разделяем на train/test (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   ✓ Тренировка: {len(X_train)} образцов")
    print(f"   ✓ Тест: {len(X_test)} образцов")
    
    # Масштабирование
    print("\n4. Масштабирование признаков...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("   ✓ StandardScaler применен")
    
    # Обучение модели
    print("\n5. Обучение RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    model.fit(X_train_scaled, y_train)
    print("   ✓ Модель обучена")
    
    # Оценка модели
    print("\n6. Оценка качества...")
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    
    metrics = {
        'train_accuracy': accuracy_score(y_train, y_pred_train),
        'test_accuracy': accuracy_score(y_test, y_pred_test),
        'precision': precision_score(y_test, y_pred_test),
        'recall': recall_score(y_test, y_pred_test),
        'f1': f1_score(y_test, y_pred_test)
    }
    
    print(f"\n   Метрики на тренировке:")
    print(f"   - Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"\n   Метрики на тесте:")
    print(f"   - Accuracy: {metrics['test_accuracy']:.4f}")
    print(f"   - Precision: {metrics['precision']:.4f}")
    print(f"   - Recall: {metrics['recall']:.4f}")
    print(f"   - F1-Score: {metrics['f1']:.4f}")
    
    # Важность признаков
    print("\n7. Важность признаков:")
    features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked']
    importances = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in importances.iterrows():
        print(f"   - {row['feature']}: {row['importance']:.4f}")
    
    return model, scaler, metrics

if __name__ == '__main__':
    model, scaler, metrics = train_titanic_model()
    
    # Сохраняем результаты
    print("\n" + "=" * 60)
    print("Модель готова для сохранения")
    print("=" * 60)


# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app.py .
COPY models/ ./models/

# Указываем порт
EXPOSE 8000

# Команда для запуска
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

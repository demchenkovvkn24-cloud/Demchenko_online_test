# Онлайн тест — вебзастосунок для складання та проходження онлайн-тестів

## Запуск
    python -m venv venv
    venv\Scripts\activate        # Linux/macOS: source venv/bin/activate
    pip install -r requirements.txt
    python run.py

## Тести
    pytest -v

## Демонстраційні дані
    flask --app run create-user teacher1 <пароль> --role teacher
    flask --app run seed-demo --teacher teacher1

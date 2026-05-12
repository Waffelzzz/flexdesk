#!/bin/bash

echo "Ждём PostgreSQL"
until pg_isready -h db -p 5432; do
  echo "db:5432 - соединение не готово, ждём..."
  sleep 2
done

echo "db:5432 - accepting connections"
echo "PostgreSQL готов"

echo "Применяем миграции Alembic"
alembic upgrade head
echo "Миграции завершены"

echo "Запускаем приложение..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info --access-log

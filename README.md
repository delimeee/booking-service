# Сервис бронирования переговорных комнат

REST API для автоматизации бронирования переговорных комнат в коворкинге. Построен на FastAPI, SQLAlchemy и JWT-аутентификации.

## Возможности

- **JWT-аутентификация** — вход по логину/паролю, токен с ограниченным сроком действия
- **Разграничение прав** — две роли: `employee` (сотрудник) и `admin` (администратор)
  - Сотрудники: просмотр доступности комнат, создание и отмена **своих** бронирований
  - Администраторы: все действия сотрудника + создание комнат и слотов, отмена **любых** бронирований
- **Защита от конфликтов** — повторное бронирование одного слота на ту же дату отклоняется
- **PostgreSQL** через SQLAlchemy (по умолчанию используется SQLite)
- **Docker и docker-compose** из коробки

---

## Быстрый старт

### Вариант 1 — Docker (SQLite, самый простой)

```bash
docker build -t booking-service .
docker run -p 8000:8000 booking-service
```

### Вариант 2 — Docker Compose (с PostgreSQL)

```bash
docker-compose up --build
```

### Вариант 3 — Локально через Poetry

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

### Вариант 4 — Локально через pip

```bash
pip install fastapi uvicorn sqlalchemy argon2-cffi python-jose pydantic pydantic-settings python-multipart
uvicorn app.main:app --reload
```

После запуска сервис доступен по адресу **http://localhost:8000**.  
Интерактивная документация (Swagger UI): **http://localhost:8000/docs**

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

| Переменная | Значение по умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./booking.db` | Строка подключения SQLAlchemy |
| `SECRET_KEY` | *(обязательно сменить!)* | Секрет для подписи JWT |
| `ALGORITHM` | `HS256` | Алгоритм JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Время жизни токена (в минутах) |

Для PostgreSQL: `DATABASE_URL=postgresql://user:pass@host:5432/dbname`

---

## Начальные данные

При первом запуске сервис автоматически создаёт тестовых пользователей и три переговорные комнаты со слотами.

| Логин | Пароль | Роль |
|---|---|---|
| `admin` | `admin123` | Администратор |
| `employee1` | `employee123` | Сотрудник |

---

## API

### Аутентификация

| Метод | Эндпоинт | Описание |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Регистрация нового пользователя |
| `POST` | `/api/v1/auth/login` | Вход, получение JWT-токена |
| `GET` | `/api/v1/auth/me` | Информация о текущем пользователе |

### Переговорные комнаты

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/rooms` | Список всех комнат |
| `POST` | `/api/v1/rooms` | Создать комнату *(только admin)* |
| `GET` | `/api/v1/rooms/{id}` | Детали комнаты |
| `POST` | `/api/v1/rooms/{id}/slots` | Добавить временной слот *(только admin)* |

### Бронирования

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/bookings/availability?date=ГГГГ-ММ-ДД` | Доступность всех комнат на дату |
| `POST` | `/api/v1/bookings` | Создать бронирование |
| `GET` | `/api/v1/bookings` | Мои бронирования |
| `GET` | `/api/v1/bookings/{id}` | Просмотр брони (своей — для сотрудника; любой — для admin) |
| `DELETE` | `/api/v1/bookings/{id}` | Отменить бронь (свою — для сотрудника; любую — для admin) |

---

## Примеры использования

```bash
BASE=http://localhost:8000/api/v1

# 1. Войти как администратор и получить токен
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d "username=admin&password=admin123" | jq -r .access_token)

# 2. Посмотреть список комнат
curl -s $BASE/rooms -H "Authorization: Bearer $TOKEN" | jq .

# 3. Проверить доступность на дату
curl -s "$BASE/bookings/availability?date=2030-06-15" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 4. Забронировать слот (room_id и slot_id из шага 3)
curl -s -X POST $BASE/bookings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"room_id": 1, "slot_id": 1, "date": "2030-06-15"}' | jq .

# 5. Посмотреть свои бронирования
curl -s $BASE/bookings -H "Authorization: Bearer $TOKEN" | jq .

# 6. Отменить бронирование
curl -s -X DELETE $BASE/bookings/1 -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Запуск тестов

```bash
# Все тесты
pytest

# С отчётом о покрытии
pytest --cov=app --cov-report=term-missing

# Только юнит-тесты
pytest tests/unit/

# Только интеграционные тесты
pytest tests/integration/
```

---

## Структура проекта

```
booking-service/
├── app/
│   ├── api/
│   │   ├── deps.py                  # Зависимости FastAPI (аутентификация, права)
│   │   └── v1/
│   │       ├── router.py            # Агрегатор роутеров
│   │       └── endpoints/
│   │           ├── auth.py          # Вход, регистрация, /me
│   │           ├── rooms.py         # CRUD комнат и слотов
│   │           └── bookings.py      # CRUD бронирований и доступность
│   ├── core/
│   │   ├── config.py                # Настройки приложения (pydantic-settings)
│   │   ├── exceptions.py            # HTTP-исключения
│   │   └── security.py              # JWT + хэширование паролей (argon2)
│   ├── db/
│   │   ├── session.py               # SQLAlchemy engine и сессия
│   │   └── init_db.py               # Начальные данные (seed)
│   ├── models/
│   │   └── models.py                # ORM-модели: User, Room, TimeSlot, Booking
│   ├── schemas/
│   │   └── schemas.py               # Pydantic-схемы запросов и ответов
│   ├── services/
│   │   ├── user_service.py          # Бизнес-логика пользователей
│   │   ├── room_service.py          # Бизнес-логика комнат
│   │   └── booking_service.py       # Бизнес-логика бронирований
│   └── main.py                      # Фабрика приложения + lifespan
├── tests/
│   ├── conftest.py                  # Фикстуры pytest
│   ├── unit/
│   │   ├── test_security.py         # Тесты JWT и хэширования
│   │   └── test_services.py         # Тесты сервисного слоя
│   └── integration/
│       └── test_api.py              # Сквозные тесты HTTP API
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

# Internal Admin CRM

Внутренняя CRM/админка для управления клиентами, сделками и задачами.

Проект сделан как fullstack-практика для прокачки backend, frontend, SQL, Docker, Redis, тестов и CI.

## Стек

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async
- Alembic
- PostgreSQL
- Redis
- JWT access/refresh tokens
- Pytest
- Ruff
- Black

### Frontend

- React
- TypeScript
- Vite
- React Router
- Axios
- Vitest
- Testing Library

### Infrastructure

- Docker Compose
- GitHub Actions CI
- PostgreSQL service
- Redis service

---

## Основной функционал

### Auth

- Регистрация пользователя
- Login
- Logout
- JWT access token
- JWT refresh token
- Refresh token blacklist через Redis
- Rate limit на login endpoint через Redis
- Роли:
  - `admin`
  - `manager`
  - `viewer`

### Clients

- Список клиентов
- Поиск по имени, телефону и email
- Фильтр по статусу
- Пагинация
- Создание клиента
- Редактирование клиента
- Soft delete через `deleted_at`

### Deals

- Список сделок
- Фильтр по статусу, клиенту и менеджеру
- Создание сделки
- Назначение менеджера
- Редактирование сделки
- Удаление сделки
- Автоматическое заполнение `closed_at`:
  - `won` / `lost` → `closed_at = now()`
  - `new` / `in_progress` → `closed_at = null`

### Tasks

- Список задач
- Создание задачи
- Назначение пользователю
- Фильтр “мои задачи”
- Просроченные задачи
- Смена статуса
- Удаление задачи

### Dashboard

- Общая статистика по клиентам
- Общая статистика по сделкам
- Статистика по задачам
- Redis cache для dashboard statistics

---

## Роли и права

### admin

Может всё:

- смотреть все данные;
- создавать;
- редактировать;
- удалять.

### manager

Может:

- смотреть клиентов;
- создавать клиентов;
- редактировать клиентов;
- создавать сделки;
- смотреть свои сделки;
- редактировать свои сделки;
- создавать задачи;
- смотреть свои задачи.

### viewer

Может только смотреть данные.

Не может:

- создавать;
- редактировать;
- удалять.

---

## Структура проекта

```text
internal-admin-crm/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── common/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── api/
│   ├── tests/
│   ├── alembic/
│   ├── sql/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── api/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── features/
│   │   ├── types/
│   │   └── tests/
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml
├── .env.example
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Environment variables

Пример находится в файле:

```text
.env.example
```

Основные переменные:

```env
APP_NAME=Internal Admin CRM
APP_ENV=local

DATABASE_URL=postgresql+asyncpg://crm_user:crm_password@postgres:5432/internal_admin_crm

REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Запуск проекта

### 1. Запустить backend, PostgreSQL и Redis

```bash
docker compose up --build
```

### 2. Применить миграции

В другом терминале:

```bash
docker compose exec backend alembic upgrade head
```

### 3. Проверить backend

```text
http://localhost:8000/health
http://localhost:8000/health/db
http://localhost:8000/health/redis
```

Ожидаемые ответы:

```json
{"status":"ok"}
```

```json
{"database":"ok"}
```

```json
{"redis":"ok"}
```

### 4. Запустить frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен по адресу:

```text
http://localhost:5173
```

---

### Seed data

Чтобы создать тестовые данные:

```bash
docker compose exec backend python -m app.scripts.seed
```

Скрипт создаст:

admin@example.com / admin12345
manager@example.com / manager12345
viewer@example.com / viewer12345
тестовых клиентов;
тестовые сделки;
тестовые задачи.

---

# 4. Запусти seed

Backend должен быть поднят:

```bash
docker compose up
```



## Тестовый пользователь

Если база пустая, можно создать admin-пользователя:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin12345",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

Данные для входа:

```text
email: admin@example.com
password: admin12345
```

---

## Backend API

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## Auth endpoints

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

---

## Clients endpoints

```text
GET    /api/v1/clients
POST   /api/v1/clients
GET    /api/v1/clients/{client_id}
PATCH  /api/v1/clients/{client_id}
DELETE /api/v1/clients/{client_id}
```

---

## Deals endpoints

```text
GET    /api/v1/deals
POST   /api/v1/deals
GET    /api/v1/deals/{deal_id}
PATCH  /api/v1/deals/{deal_id}
DELETE /api/v1/deals/{deal_id}
```

### Deal statistics

```text
GET /api/v1/deals/stats/summary
GET /api/v1/deals/stats/conversion
GET /api/v1/deals/stats/top-managers
```

---

## Tasks endpoints

```text
GET    /api/v1/tasks
POST   /api/v1/tasks
GET    /api/v1/tasks/{task_id}
PATCH  /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}

GET    /api/v1/tasks/my
GET    /api/v1/tasks/overdue
```

---

## Dashboard endpoint

```text
GET /api/v1/dashboard/stats
```

---

## SQL requirements

В проекте реализованы:

- JOIN между `clients`, `deals`, `users`;
- агрегация `SUM` сделок по менеджерам;
- `GROUP BY` по статусам;
- индексы на часто используемые поля;
- минимум 2 raw SQL запроса;
- `EXPLAIN ANALYZE` тяжелого запроса;
- описание `EXPLAIN` в README.

---

## Raw SQL

Raw SQL используется для:

### 1. Общей статистики сделок

Файл:

```text
backend/app/repositories/deal_repository.py
```

Метод:

```text
get_summary_stats
```

### 2. Топ менеджеров по выигранным сделкам

Файл:

```text
backend/app/repositories/deal_repository.py
```

Метод:

```text
get_top_managers
```

---

## EXPLAIN ANALYZE

Для анализа тяжелого SQL-запроса используется запрос топ-5 менеджеров по сумме выигранных сделок за период.

Файл запроса:

```text
backend/sql/explain_top_managers.sql
```

Запуск:

```bash
docker compose exec -T postgres psql -U crm_user -d internal_admin_crm < backend/sql/explain_top_managers.sql
```

Анализируемый запрос:

```sql
SELECT
    u.id AS manager_id,
    u.full_name AS manager_name,
    u.email AS manager_email,
    COUNT(d.id) AS deals_count,
    COALESCE(SUM(d.amount), 0) AS total_amount
FROM deals d
JOIN users u ON u.id = d.manager_id
JOIN clients c ON c.id = d.client_id
WHERE d.status = 'won'
  AND c.deleted_at IS NULL
  AND d.closed_at::date >= DATE '2026-05-01'
  AND d.closed_at::date <= DATE '2026-05-31'
GROUP BY u.id, u.full_name, u.email
ORDER BY total_amount DESC
LIMIT 5;
```

### Что делает запрос

Запрос соединяет таблицы:

- `deals`
- `users`
- `clients`

Он выбирает только выигранные сделки со статусом `won`, исключает удаленных клиентов через `clients.deleted_at IS NULL`, группирует результат по менеджерам и считает:

- количество выигранных сделок;
- общую сумму выигранных сделок.

После этого результат сортируется по сумме сделок и возвращает топ-5 менеджеров.

### Что смотреть в EXPLAIN ANALYZE

В результате анализа нужно обратить внимание на:

- `Execution Time` — фактическое время выполнения запроса;
- `Planning Time` — время построения плана;
- тип сканирования таблиц: `Seq Scan`, `Index Scan`, `Bitmap Index Scan`;
- тип соединения таблиц: `Hash Join`, `Nested Loop`, `Merge Join`;
- этап агрегации: `HashAggregate` или `GroupAggregate`;
- использование памяти и буферов в блоке `BUFFERS`.

### Вывод

На небольшом объеме данных PostgreSQL может использовать `Seq Scan`, потому что последовательное чтение маленькой таблицы дешевле, чем обращение к индексам.

При росте количества сделок основную нагрузку будет создавать фильтрация по:

- `deals.status`;
- `deals.closed_at`;
- `deals.manager_id`;
- `deals.client_id`.

Для оптимизации такого запроса в проекте уже используются индексы на часто фильтруемые поля. Если данных станет много, можно дополнительно добавить составной индекс для аналитического запроса, например по `status`, `closed_at` и `manager_id`.

---

## Redis

Redis используется только для трех задач:

### 1. Dashboard cache

Ключ:

```text
dashboard:stats
```

Проверка:

```bash
docker compose exec redis redis-cli GET dashboard:stats
docker compose exec redis redis-cli TTL dashboard:stats
```

### 2. Refresh token blacklist

Ключи:

```text
auth:refresh_blacklist:*
```

Проверка:

```bash
docker compose exec redis redis-cli KEYS "auth:refresh_blacklist:*"
```

### 3. Login rate limit

Ключи:

```text
auth:login_rate_limit:*
```

Проверка:

```bash
docker compose exec redis redis-cli KEYS "auth:login_rate_limit:*"
```

---

## Backend tests

Запуск:

```bash
docker compose exec backend pytest -v
```

Ожидаемо:

```text
14 passed
```

---

## Backend lint and format

Проверка форматирования:

```bash
docker compose exec backend black --check app tests
```

Автоформатирование:

```bash
docker compose exec backend black app tests
```

Проверка Ruff:

```bash
docker compose exec backend ruff check app tests
```

Автофикс Ruff:

```bash
docker compose exec backend ruff check app tests --fix
```

---

## Frontend tests

Запуск:

```bash
cd frontend
npm run test:run
```

---

## Frontend build

```bash
cd frontend
npm run build
```

---

## GitHub Actions CI

CI находится в файле:

```text
.github/workflows/ci.yml
```

CI проверяет:

### Backend

- установку зависимостей;
- Black;
- Ruff;
- Alembic migrations;
- Pytest;
- PostgreSQL service;
- Redis service.

### Frontend

- `npm ci`;
- frontend build;
- frontend tests.

---

## Полная локальная проверка

### Backend

```bash
docker compose down
docker compose up --build
```

В другом терминале:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend black --check app tests
docker compose exec backend ruff check app tests
docker compose exec backend pytest -v
```

### Frontend

```bash
cd frontend
npm run build
npm run test:run
```

---

## Основные страницы frontend

```text
/login
/dashboard
/clients
/clients/:id
/deals
/tasks
```

---

## Что можно показать на собеседовании

В проекте есть:

- layered architecture: router → service → repository;
- async SQLAlchemy;
- PostgreSQL migrations через Alembic;
- JWT auth;
- role-based access;
- Redis cache;
- Redis blacklist;
- Redis rate limit;
- raw SQL;
- JOIN;
- GROUP BY;
- SUM aggregation;
- EXPLAIN ANALYZE;
- backend tests;
- frontend tests;
- Docker Compose;
- GitHub Actions CI;
- React + TypeScript SPA.

---

## Возможные улучшения

Что можно добавить позже:

- нормальный refresh flow на frontend;
- protected routes на frontend;
- toast-уведомления;
- React Query;
- полноценные select-поля вместо ручного ввода `client_id`, `manager_id`, `deal_id`;
- отдельную страницу пользователей;
- больше frontend-тестов;
- observability: structured logs, metrics, tracing.

Пока эти улучшения специально не добавлены, чтобы не усложнять проект раньше времени.
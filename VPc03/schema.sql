-- Таблица участников
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    birth_date DATE NOT NULL,   -- возраст проверяется приложением или триггером
    registration_date DATE DEFAULT (date('now'))
);

-- Тренеры
CREATE TABLE IF NOT EXISTS trainers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    specialization TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    hire_date DATE DEFAULT (date('now'))
);

-- Типы занятий (шаблоны)
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    trainer_id INTEGER REFERENCES trainers(id) ON DELETE SET NULL,
    typical_duration INTEGER NOT NULL DEFAULT 60,
    default_capacity INTEGER NOT NULL CHECK(default_capacity > 0)
);

-- Конкретные сессии по расписанию
CREATE TABLE IF NOT EXISTS class_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    trainer_id INTEGER REFERENCES trainers(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL CHECK(end_time > start_time),
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    location TEXT DEFAULT 'Main Hall',
    UNIQUE(class_id, start_time)   -- исключаем дубли расписания
);

-- Абонементы (история)
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id),
    type TEXT NOT NULL CHECK(type IN ('месячный','квартальный','годовой','пробный')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL CHECK(end_date > start_date),
    payment_id INTEGER REFERENCES payments(id)
);

-- Оплаты
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id),
    amount DECIMAL(10,2) NOT NULL CHECK(amount > 0),
    payment_date TIMESTAMP DEFAULT (datetime('now')),
    payment_method TEXT DEFAULT 'card'
);

-- Посещения
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id),
    session_id INTEGER NOT NULL REFERENCES class_sessions(id),
    check_in_time TIMESTAMP DEFAULT (datetime('now')),
    UNIQUE(member_id, session_id)
);

-- Индексы для ускорения
CREATE INDEX IF NOT EXISTS idx_sessions_start ON class_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_trainer ON class_sessions(trainer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_class ON class_sessions(class_id);
CREATE INDEX IF NOT EXISTS idx_visits_member ON visits(member_id);
CREATE INDEX IF NOT EXISTS idx_visits_session ON visits(session_id);
CREATE INDEX IF NOT EXISTS idx_memberships_member ON memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_payments_member ON payments(member_id);
-- 1. Активные абонементы на сегодня
SELECT m.full_name, mbs.type, mbs.end_date
FROM members m
JOIN memberships mbs ON m.id = mbs.member_id
WHERE mbs.start_date <= date('now') AND mbs.end_date >= date('now');

-- 2. Количество записанных на занятия по датам
SELECT date(cs.start_time) AS session_date, COUNT(v.id) AS total_visits
FROM class_sessions cs
LEFT JOIN visits v ON cs.id = v.session_id
GROUP BY session_date
ORDER BY session_date;

-- 3. Тренеры и их классы (включая сессии)
SELECT t.full_name AS trainer, c.name AS class, COUNT(cs.id) AS sessions_count
FROM trainers t
LEFT JOIN classes c ON c.trainer_id = t.id
LEFT JOIN class_sessions cs ON cs.class_id = c.id
GROUP BY t.full_name, c.name
ORDER BY t.full_name;

-- 4. Участники, не посещавшие клуб более 30 дней
SELECT m.full_name, MAX(v.check_in_time) AS last_visit
FROM members m
LEFT JOIN visits v ON m.id = v.member_id
GROUP BY m.id
HAVING last_visit IS NULL OR last_visit < datetime('now', '-30 days');

-- 5. Топ-3 популярных занятий по количеству посещений
SELECT c.name, COUNT(v.id) AS visit_count
FROM classes c
JOIN class_sessions cs ON cs.class_id = c.id
JOIN visits v ON v.session_id = cs.id
GROUP BY c.id
ORDER BY visit_count DESC
LIMIT 3;

-- 6. Доход клуба по типам абонементов
SELECT mbs.type, SUM(p.amount) AS total_revenue
FROM payments p
JOIN memberships mbs ON mbs.payment_id = p.id
GROUP BY mbs.type
ORDER BY total_revenue DESC;

-- 7. Конфликты расписания (участник записан на пересекающиеся сессии)
SELECT v1.member_id, m.full_name,
       cs1.start_time AS first_start, cs1.end_time AS first_end,
       cs2.start_time AS second_start, cs2.end_time AS second_end
FROM visits v1
JOIN class_sessions cs1 ON v1.session_id = cs1.id
JOIN visits v2 ON v1.member_id = v2.member_id
JOIN class_sessions cs2 ON v2.session_id = cs2.id
JOIN members m ON v1.member_id = m.id
WHERE v1.id < v2.id
  AND cs1.start_time < cs2.end_time
  AND cs2.start_time < cs1.end_time;

-- 8. Самый загруженный тренер по количеству проведённых сессий
SELECT t.full_name, COUNT(cs.id) AS conducted_sessions
FROM trainers t
LEFT JOIN class_sessions cs ON cs.trainer_id = t.id
GROUP BY t.id
ORDER BY conducted_sessions DESC
LIMIT 1;
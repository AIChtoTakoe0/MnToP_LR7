# Задание 3. Выборка данных из таблиц: WHERE, ORDER BY, JOIN, GROUP BY.
#
# Запуск (из этой папки):  python task3_select.py

import sqlite3

DB_PATH = "school.db"


def init_db(path: str) -> sqlite3.Connection:
    """Создаёт БД с таблицами и данными (копия функции из задания 1)."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            group_name TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id    INTEGER PRIMARY KEY,
            title TEXT    NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS grades (
            id         INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            grade      INTEGER NOT NULL CHECK (grade BETWEEN 2 AND 5),
            UNIQUE (student_id, subject_id)
        );
        INSERT OR IGNORE INTO students (id, name, group_name) VALUES
            (1, 'Иванов Иван',  'ИТ-21'),
            (2, 'Петрова Анна', 'ИТ-22'),
            (3, 'Сидоров Пётр', 'ИТ-21');
        INSERT OR IGNORE INTO subjects (id, title) VALUES
            (1, 'Математика'), (2, 'Программирование'), (3, 'Базы данных');
        INSERT OR IGNORE INTO grades (id, student_id, subject_id, grade) VALUES
            (1, 1, 1, 5), (2, 1, 2, 4),
            (3, 2, 1, 5), (4, 2, 3, 5),
            (5, 3, 1, 3), (6, 3, 2, 4);
    """)
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = init_db(DB_PATH)
    cur = conn.cursor()

    print("1) Все студенты с сортировкой (ORDER BY):")
    for row in cur.execute("SELECT id, name, group_name FROM students ORDER BY name"):
        print("   ", row)

    print("\n2) Оценки не ниже 4 (WHERE + JOIN со справочниками):")
    query = """
        SELECT s.name, sub.title, g.grade
        FROM grades g
        JOIN students  s   ON s.id    = g.student_id
        JOIN subjects  sub ON sub.id  = g.subject_id
        WHERE g.grade >= 4
        ORDER BY g.grade DESC, s.name
    """
    for name, subject, grade in cur.execute(query):  # кортеж строки можно распаковать
        print(f"    {name}: {subject} — {grade}")

    print("\n3) Средний балл каждого студента (GROUP BY + агрегат AVG):")
    query = """
        SELECT s.name, ROUND(AVG(g.grade), 2) AS avg_grade
        FROM grades g
        JOIN students s ON s.id = g.student_id
        GROUP BY s.id, s.name
        ORDER BY avg_grade DESC
    """
    for name, avg in cur.execute(query):
        print(f"    {name}: {avg}")

    print("\n4) Один студент по id (параметризованный запрос + fetchone):")
    # Знак ? — подстановка параметра средствами sqlite3 (защита от SQL-инъекций).
    # НИКОГДА не подставляйте значения в строку запроса через f-строки.
    row = cur.execute(
        "SELECT name, group_name FROM students WHERE id = ?", (2,)
    ).fetchone()  # fetchone — первая строка результата (или None)
    print("    Найден:", row)

    conn.close()

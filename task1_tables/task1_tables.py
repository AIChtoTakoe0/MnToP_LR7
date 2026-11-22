# Задание 1. Создание нескольких таблиц в SQLite (встроенный модуль sqlite3).
#
# Запуск (из этой папки):  python task1_tables.py
# Результат: файл school.db с тремя связанными таблицами и тестовыми данными.
# Функция init_db() используется (в копии) также в заданиях 2 и 3 — поэтому
# любой скрипт лабораторной можно запустить первым, БД создастся сама.

import sqlite3

DB_PATH = "school.db"


def init_db(path: str) -> sqlite3.Connection:
    """Создаёт БД с тремя таблицами и наполняет её, если она ещё пуста."""
    # connect создаёт файл БД, если его нет, и возвращает соединение
    conn = sqlite3.connect(path)
    # В SQLite проверка внешних ключей по умолчанию ВЫКЛЮЧЕНА;
    # прагма включает её для текущего соединения
    conn.execute("PRAGMA foreign_keys = ON")
    # executescript выполняет несколько SQL-операторов одним вызовом
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (           -- студенты
            id         INTEGER PRIMARY KEY,              -- автоинкрементный ключ
            name       TEXT    NOT NULL,
            group_name TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subjects (           -- предметы (справочник)
            id    INTEGER PRIMARY KEY,
            title TEXT    NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS grades (             -- оценки: связывает две таблицы
            id         INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            grade      INTEGER NOT NULL CHECK (grade BETWEEN 2 AND 5),
            UNIQUE (student_id, subject_id)             -- одна оценка по предмету
        );

        INSERT OR IGNORE INTO students (id, name, group_name) VALUES
            (1, 'Иванов Иван',  'ИТ-21'),
            (2, 'Петрова Анна', 'ИТ-22'),
            (3, 'Сидоров Пётр', 'ИТ-21');

        INSERT OR IGNORE INTO subjects (id, title) VALUES
            (1, 'Математика'), (2, 'Программирование'), (3, 'Базы данных');

        INSERT OR IGNORE INTO grades (id, student_id, subject_id, grade) VALUES
            (1, 1, 1, 5), (2, 1, 2, 4),   -- Иванов:  математика 5, программирование 4
            (3, 2, 1, 5), (4, 2, 3, 5),   -- Петрова: математика 5, базы данных 5
            (5, 3, 1, 3), (6, 3, 2, 4);   -- Сидоров: математика 3, программирование 4
    """)
    # commit фиксирует изменения; без него они не сохранятся в файле БД
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = init_db(DB_PATH)
    cur = conn.cursor()

    # sqlite_master — служебная таблица: в ней перечислены все таблицы БД
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    print("Таблицы в БД:", tables)

    for table in tables:
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} строк")

    conn.close()  # закрытие соединения

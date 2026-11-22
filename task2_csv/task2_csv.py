# Задание 2. Экспорт данных из SQLite в CSV (модуль csv стандартной библиотеки).
#
# Запуск (из этой папки):  python task2_csv.py
# Результат: export.csv с объединённой выборкой из трёх таблиц задания 1.
# Функция init_db() — копия из задания 1: БД создаётся сама, если её нет.

import csv
import sqlite3

DB_PATH = "school.db"
CSV_PATH = "export.csv"


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


def export_to_csv(conn: sqlite3.Connection, csv_path: str) -> int:
    """Сохраняет результат SQL-запроса в CSV. Возвращает число строк."""
    cur = conn.cursor()
    # JOIN соединяет три таблицы: оценка -> студент -> предмет
    cur.execute("""
        SELECT g.id, s.name AS student, sub.title AS subject, g.grade
        FROM grades g
        JOIN students s  ON s.id  = g.student_id
        JOIN subjects sub ON sub.id = g.subject_id
        ORDER BY s.name, sub.title
    """)
    # cursor.description хранит имена колонок результата запроса
    headers = [d[0] for d in cur.description]
    rows = cur.fetchall()  # все строки результата одним списком

    # newline="" обязателен: без него в Windows появятся пустые строки
    # encoding="utf-8-sig" добавляет BOM — Excel откроет кириллицу без «кракозябр»
    # delimiter=";" — CSV с таким разделителем Excel в русской локали
    # открывает по двойному щелчку
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)  # строка заголовков
        writer.writerows(rows)    # все данные одним вызовом
    return len(rows)


if __name__ == "__main__":
    conn = init_db(DB_PATH)
    n = export_to_csv(conn, CSV_PATH)
    print(f"Экспортировано строк: {n} -> {CSV_PATH}")

    # Контрольная проверка: читаем файл обратно
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        print("--- содержимое export.csv ---")
        print(f.read())
    conn.close()

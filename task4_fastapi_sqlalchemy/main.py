# Задание 4. REST API на FastAPI + SQLAlchemy ORM.
#
# Запуск (из этой папки):  uvicorn main:app --reload
# Swagger:                 http://127.0.0.1:8000/docs
#
# Эндпоинты (CRUD по студентам):
#   GET    /students       список
#   GET    /students/{id}  один студент
#   POST   /students       создать   {"name": "...", "group_name": "...", "rating": 4.5}
#   PUT    /students/{id}  изменить
#   DELETE /students/{id}  удалить

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Float, String, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

# СУБД задаётся строкой подключения. Сейчас — файл SQLite: для лабораторной
# работает без отдельного сервера.
SQLALCHEMY_URL = "sqlite:///students.db"
# Для PostgreSQL из теоретической части строка имела бы вид (нужен запущенный
# сервер PostgreSQL и пакет psycopg2-binary: pip install psycopg2-binary).
# Вариант с PostgreSQL в этой работе не проверен запуском — сервер не установлен:
# SQLALCHEMY_URL = "postgresql+psycopg2://postgres:ПАРОЛЬ@localhost:5432/students_db"
# Остальной код при смене СУБД не меняется — в этом главный смысл ORM.

# create_engine — «фабрика соединений» с БД.
# check_same_thread=False нужен именно для SQLite: FastAPI выполняет обычные
# (sync) обработчики в пуле потоков, а sqlite3 по умолчанию запрещает
# использовать одно соединение из разных потоков.
engine = create_engine(SQLALCHEMY_URL, connect_args={"check_same_thread": False})

# sessionmaker — фабрика сессий. Сессия в SQLAlchemy — «рабочий блокнот» объектов
# и одновременно граница транзакции (подробнее в задании 5).
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


class Student(Base):
    """Модель: класс = таблица students, атрибуты = колонки."""
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)              # PRIMARY KEY
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    group_name: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


# Создаёт таблицы из всех моделей, если их ещё нет (= CREATE TABLE IF NOT EXISTS)
Base.metadata.create_all(engine)


# --- Pydantic-схемы описывают JSON на входе и выходе API ---
class StudentIn(BaseModel):
    """Тело запроса при создании/изменении (без id — его выдаёт БД)."""
    name: str
    group_name: str
    rating: float


class StudentOut(StudentIn):
    """Ответ API: то же + id. from_attributes разрешает строить схему
    прямо из ORM-объекта Student."""
    id: int
    model_config = ConfigDict(from_attributes=True)


def get_session():
    """FastAPI-зависимость: на каждый запрос выдаётся свежая сессия,
    которая гарантированно закрывается после ответа (yield-синтаксис)."""
    with SessionLocal() as session:
        yield session


app = FastAPI(title="Students API",
              description="Лабораторная 7, задание 4: FastAPI + SQLAlchemy ORM")


@app.get("/students", response_model=list[StudentOut])
def list_students(session: Session = Depends(get_session)):
    # select() — современный стиль запросов SQLAlchemy (начиная с 2.0)
    return session.scalars(select(Student)).all()


@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int, session: Session = Depends(get_session)):
    # session.get — выборка по первичному ключу
    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student


@app.post("/students", response_model=StudentOut, status_code=201)
def create_student(data: StudentIn, session: Session = Depends(get_session)):
    student = Student(**data.model_dump())
    session.add(student)      # пометить новый объект для сохранения
    session.commit()          # зафиксировать транзакцию — INSERT уходит в БД
    session.refresh(student)  # перечитать из БД (получить сгенерированный id)
    return student


@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentIn,
                   session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    for field, value in data.model_dump().items():
        setattr(student, field, value)  # изменение атрибута = UPDATE при commit
    session.commit()
    session.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    session.delete(student)
    session.commit()  # DELETE; статус 204 — тела ответа нет

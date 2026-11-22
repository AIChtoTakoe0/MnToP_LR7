# Задание 5. Транзакции: commit и rollback (sqlite3 и SQLAlchemy).
#
# Запуск (из этой папки):  python task5_transactions.py
#
# Транзакция — группа операций с БД по принципу «всё или ничего»:
# либо фиксируются все изменения (commit), либо отменяются все (rollback).
# В sqlite3 транзакция открывается автоматически перед первым изменением
# данных и живёт до conn.commit() / conn.rollback().

import sqlite3

from sqlalchemy import Float, String, create_engine, delete, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
)


# ---------- Часть A. Транзакции через sqlite3 ----------

def part_a() -> None:
    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    # CHECK запрещает отрицательный баланс на уровне самой БД
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id      INTEGER PRIMARY KEY,
            owner   TEXT NOT NULL,
            balance REAL NOT NULL CHECK (balance >= 0)
        );
        DELETE FROM accounts;             -- сброс данных для повторных запусков
        INSERT INTO accounts (id, owner, balance) VALUES
            (1, 'Иванов',  1000.0),
            (2, 'Петрова',  500.0);
    """)
    conn.commit()  # подготовка данных зафиксирована — это отдельная транзакция

    def balances(title: str) -> None:
        print(title)
        for row in cur.execute("SELECT id, owner, balance FROM accounts ORDER BY id"):
            print(f"    счёт {row[0]} ({row[1]}): {row[2]}")

    def transfer(from_id: int, to_id: int, amount: float) -> None:
        """Перевод двумя UPDATE. Между ними транзакция ещё НЕ закрыта."""
        cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?",
                    (amount, from_id))
        n = cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?",
                        (amount, to_id)).rowcount  # сколько строк изменилось
        if n == 0:  # счёт получателя не найден: списание «в никуда»
            raise ValueError(f"Счёт получателя {to_id} не найден")

    balances("A. Начальные остатки:")

    # Успешный сценарий: оба UPDATE выполняются и фиксируются вместе
    transfer(1, 2, 300)
    conn.commit()
    balances("A. После перевода 300 и conn.commit():")

    # Неудачный сценарий: первый UPDATE уже выполнен ВНУТРИ транзакции,
    # второй завершается ошибкой (счёт 99 не существует).
    # rollback отменяет ВСЁ с начала транзакции — деньги не «исчезают».
    try:
        transfer(1, 99, 200)
        conn.commit()
    except ValueError as e:
        print("A. Ошибка:", e)
        conn.rollback()  # баланс Иванова вернётся к состоянию после commit
    balances("A. После неудачного перевода и conn.rollback():")
    conn.close()


# ---------- Часть B. Транзакции через SQLAlchemy (сессии) ----------

class Base(DeclarativeBase):
    pass


class Account(Base):
    """Модель счёта: таблица accounts_orm."""
    __tablename__ = "accounts_orm"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(100))
    balance: Mapped[float] = mapped_column(Float)


def part_b() -> None:
    engine = create_engine("sqlite:///bank_orm.db")
    Base.metadata.create_all(engine)

    with Session(engine) as session:  # блок with закрывает сессию гарантированно
        # сброс данных для повторных запусков
        session.execute(delete(Account))
        session.add_all([
            Account(owner="Иванов", balance=1000.0),
            Account(owner="Петрова", balance=500.0),
        ])
        session.commit()  # фиксация: объекты сохранены в БД

        # select().where() — фильтрация в стиле SQLAlchemy 2.x
        sender = session.scalars(
            select(Account).where(Account.owner == "Иванов")).one()
        sender.balance -= 200  # изменение пока существует ТОЛЬКО в сессии

        receiver = session.scalars(
            select(Account).where(Account.owner == "Нет такого")).first()
        if receiver is None:
            print("B. Получатель не найден — session.rollback()")
            session.rollback()  # откат: изменение sender отброшено
            # объекты после rollback «устарели»; обращение к атрибуту
            # заставляет SQLAlchemy перечитать значение из БД
            print(f"B. Баланс Иванова после отката: {sender.balance} "
                  f"(изменение отменено)")
        else:
            session.commit()


if __name__ == "__main__":
    part_a()
    print()
    part_b()

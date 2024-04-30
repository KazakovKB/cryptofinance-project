import os
import telebot
from sqlalchemy.sql import func
from sqlalchemy import (
    MetaData, Table, Column, SMALLINT, Integer,
    BigInteger, String, Boolean, Date, create_engine,
    TIMESTAMP, TEXT, ForeignKey, Numeric
)


def alert(message):
    bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')


def main():
    with engine.begin() as conn:
        try:
            conn.execute(users_table.update().values(subscription=False)
                         .where(users_table.c.subscription_end == func.current_date()))
        except Exception as e:
            alert('*UPDATE subscription:* ошибка при запросе UPDATE\n{}'.format(e))
            raise


if __name__ == '__main__':
    engine = create_engine(
        os.environ.get('MY_POSTGRES')
    )

    bot = telebot.TeleBot(os.environ.get('MY_TELEGRAM'))
    chat_id = os.environ.get('MY_ID')

    # Создание объекта метаданных
    meta = MetaData()

    # Описание таблицы пользователей
    users_table = Table(
        'users',
        meta,
        Column('user_id', BigInteger, primary_key=True),
        Column('first_name', String(64)),
        Column('last_name', String(64)),
        Column('is_premium', Boolean),
        Column('language_code', String(10)),
        Column('username', String(64)),
        Column('is_bot', Boolean),
        Column('gpt_limit', SMALLINT, default=10),
        Column('newsletter', Boolean, default=True),
        Column('subscription', Boolean, default=True),
        Column('subscription_end', Date)
    )
    # Описание таблицы заказов
    orders_table = Table(
        'orders', meta,
        Column('id', BigInteger, primary_key=True),
        Column('external_id', String(255), unique=True, nullable=False),
        Column('order_number', String(24), unique=True, nullable=False),
        Column('amount', Numeric(10, 2), nullable=False),
        Column('currency_code', String(3), nullable=False),
        Column('description', TEXT),
        Column('status', String(50), nullable=False),
        Column('created_at', TIMESTAMP(timezone=True), default=func.current_timestamp()),
        Column('updated_at', TIMESTAMP(timezone=True), default=func.current_timestamp(),
               onupdate=func.current_timestamp()),
        Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False)
    )

    main()
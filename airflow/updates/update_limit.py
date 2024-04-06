import os
import telebot
from sqlalchemy import (
    create_engine, Table, BigInteger,
    Column, String, MetaData, Boolean, SMALLINT
)


def alert(message):
    bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')


def main():
    with engine.begin() as conn:
        try:
            conn.execute(users_table.update().values(gpt_limit=20))
        except Exception as e:
            alert('*UPDATE LIMIT:* ошибка при запросе UPDATE\n{}'.format(e))
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
        Column('subscription', Boolean, default=True)
    )

    main()

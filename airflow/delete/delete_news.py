import os
import telebot
from sqlalchemy.dialects.postgresql import INTERVAL
from sqlalchemy import (
    create_engine, Date, Table, func,
    Column, String, MetaData, TEXT, Boolean
)


def alert(message):
    bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')


def main():
    with engine.begin() as conn:
        try:
            # Текущая дата минус 3 дня
            threshold_date = func.current_date() - func.cast('3 days', INTERVAL)

            # Формируем запрос на удаление
            delete = articles_table.delete().where(articles_table.c.date < threshold_date)

            # Выполняем запрос
            conn.execute(delete)
        except Exception as e:
            alert('*DELETE news:* ошибка при запросе DELETE\n{}'.format(e))
            raise


if __name__ == '__main__':
    engine = create_engine(
        os.environ.get('MY_POSTGRES')
    )

    bot = telebot.TeleBot(os.environ.get('MY_TELEGRAM'))
    chat_id = os.environ.get('MY_ID')

    # Создание объекта метаданных
    meta = MetaData()

    # Описание таблицы
    articles_table = Table(
        'articles',
        meta,
        Column('link', String(255), primary_key=True),
        Column('title', String(255), nullable=False),
        Column('description', String, nullable=False),
        Column('date', Date, nullable=False),
        Column('article', TEXT, nullable=False),
        Column('source', String(30), nullable=False),
        Column('new', Boolean, default=True)
    )

    main()

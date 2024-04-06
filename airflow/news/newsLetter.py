import os
import telebot
from sqlalchemy import (
    create_engine, Date, Table, select, BigInteger,
    Column, String, MetaData, TEXT, Boolean, SMALLINT
)


def alert(message):
    bot.send_message(chat_id=os.environ.get('MY_ID'), text=message, parse_mode='Markdown')


def send_news():
    with engine.connect() as conn:
        try:
            query = conn.execute(select(articles_table.c.link,
                                        articles_table.c.article,
                                        articles_table.c.title,
                                        articles_table.c.source)
                                 .where(articles_table.c.new.is_(True)).limit(1))
            data = query.fetchall()

            query = conn.execute(select(users_table.c.user_id).where(users_table.c.newsletter.is_(True)))
            users_id = query.fetchall()
        except Exception as e:
            alert('*Newsletter:* ошибка при запросе SELECT\n{}'.format(e))
            return None

    if data:
        link, article, title, source = data[0][0], data[0][1], data[0][2], data[0][3]
        if source == 'CoinDesk':
            url = 'https://www.coindesk.com' + link
        else:
            url = None

        keyboard = telebot.types.InlineKeyboardMarkup()
        button = telebot.types.InlineKeyboardButton(text="Скрыть", callback_data='delete_message')
        keyboard.add(button)

        for chat_id in users_id:
            try:
                bot.send_message(
                    chat_id=chat_id[0],
                    text=f"📰 *{title}*\n\n{article}\n\nИсточник: [{source}]({url})",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            except telebot.apihelper.ApiException as e:
                if e.error_code != 403:
                    alert('*Newsletter:* ошибка при рассылке\n{}\n\nURL: {}'.format(e, url))
                else:
                    continue

        with engine.begin() as conn:
            try:
                conn.execute(articles_table.update().where(articles_table.c.link == link).values(new=False))
            except Exception as e:
                alert('*Newsletter:* ошибка при запросе UPDATE\n{}'.format(e))


if __name__ == '__main__':
    engine = create_engine(
        os.environ.get('MY_POSTGRES')
    )

    # Создание объекта метаданных
    meta = MetaData()

    # Описание таблиц
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
        Column('gpt_limit', SMALLINT, default=20),
        Column('newsletter', Boolean, default=True),
        Column('subscription', Boolean, default=False)
    )

    bot = telebot.TeleBot(os.environ.get('MY_TELEGRAM'))

    send_news()

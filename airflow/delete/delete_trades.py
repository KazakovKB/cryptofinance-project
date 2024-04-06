import os
from clickhouse_driver import Client
import telebot


def alert(message):
    bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')


def main():
    try:
        query = f"ALTER TABLE cryptofinance.agg_trades DELETE WHERE trade_time < toDate(NOW()) - INTERVAL 8 DAY"
        client.execute(query)
    except Exception as e:
        alert('*DELETE:* ошибка при запросе DELETE\n{}'.format(e))
        raise


if __name__ == '__main__':
    # Параметры подключения к ClickHouse
    database = os.environ.get('DATABASE')
    user = os.environ.get('USER')
    password = os.environ.get('PASSWORD')
    host = os.environ.get('HOST')

    # Подключение к ClickHouse
    client = Client(host=host, port=9000, user=user, password=password, database=database)

    bot = telebot.TeleBot(os.environ.get('MY_TELEGRAM'))
    chat_id = os.environ.get('MY_ID')

    main()

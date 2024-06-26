import json
from datetime import datetime, timezone
import websocket
import telebot
import logging
import os
from clickhouse_driver import Client
import numpy as np


class Liquidation:
    # Инициализация экземпляра класса
    def __init__(self, url_ws, stream_name, table, db_client_, token_, chat_id_):
        self.stream_id = np.random.randint(1, 10000)
        self.stream_name = stream_name
        self.url = url_ws
        self.table = table
        self.ws = None
        self.db_client = db_client_
        self.token = token_
        self.chat_id = chat_id_

    # Обработка сообщений, получаемых через WebSocket
    def on_message(self, ws, message):
        event = json.loads(message)
        # Обработка событий ликвидации ордеров
        if 'e' in event and event['e'] == 'forceOrder':
            # Формирование данных для вставки в базу данных
            data = event['o']
            data_to_insert = {
                'event_time': datetime.fromtimestamp(event['E'] / 1000, timezone.utc),
                'symbol': data['s'],
                'side': data['S'],
                'order_type': data['o'],
                'time_in_force': data['f'],
                'quantity': float(data['q']),
                'price': float(data['p']),
                'average_price': float(data['ap']),
                'order_status': data['X'],
                'trade_time': datetime.fromtimestamp(data['T'] / 1000, timezone.utc),
            }

            # Формирование и выполнение запроса на вставку данных в базу данных
            query = f"INSERT INTO {self.table} (*) VALUES"
            try:
                self.db_client.execute(query, [data_to_insert])
            except Exception as e:
                self.alert(f">>>Ошибка при вставке:<<<\n{e}")

    # Обработка ошибок WebSocket
    def on_error(self, ws, error):
        self.alert(error)

    # Обработка закрытия соединения WebSocket
    def on_close(self, ws, close_status_code, close_msg):
        self.alert(f"WebSocket connection closed with code: {close_status_code}, message: {close_msg}")

    # Установка соединения и подписка на поток данных при открытии WebSocket
    def on_open(self, ws):
        self.ws.send(json.dumps({"method": "SUBSCRIBE", "params": self.stream_name, "id": self.stream_id}))
        self.alert("WebSocket connected and subscribed")

    # Запуск WebSocket соединения
    def run(self):
        self.ws = websocket.WebSocketApp(self.url,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

    # Отправка уведомлений через Telegram
    def alert(self, data):
        bot = telebot.TeleBot(self.token)
        bot.send_message(text=f'*Received data from Liquidation:*\n\n {data}',
                         chat_id=self.chat_id, parse_mode='Markdown')


if __name__ == '__main__':
    # настраиваем логирование
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Параметры подключения к ClickHouse
    database = os.environ.get('DATABASE')
    user = os.environ.get('USER')
    password = os.environ.get('PASSWORD')
    host = os.environ.get('HOST')
    port = os.environ.get('PORT')

    # Подключение к ClickHouse
    db_client = Client(host=host, port=port, user=user, password=password, database=database)

    # Настраиваем Telegram Alert
    token = os.environ.get('TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    symbol = os.environ.get('SYMBOL')
    ws_client = Liquidation(
        url_ws='wss://fstream.binance.com/ws',
        stream_name=[f'{symbol}@forceOrder'],
        table='liquidation',
        db_client_=db_client,
        token_=token,
        chat_id_=chat_id
    )

    # Запуск Websocket
    ws_client.run()

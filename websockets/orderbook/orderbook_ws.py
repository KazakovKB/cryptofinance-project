import time
from sqlalchemy import create_engine, Table, Column, Float, String, MetaData, delete, tuple_
from sqlalchemy.dialects.postgresql import insert
import os
import requests
import json
import websocket
import telebot
import numpy as np
import logging


class Orderbook:
    # Инициализация экземпляра класса
    def __init__(self, url_ws, stream_name, table, engine_, token_, chat_id_, symbol_):
        self.symbol = symbol_
        self.last_update_id = False
        self.stream_id = np.random.randint(1, 10000)
        self.stream_name = stream_name
        self.url = url_ws
        self.table = table
        self.ws = None
        self.engine = engine_
        self.token = token_
        self.chat_id = chat_id_

    # Обработка сообщений, получаемых через WebSocket
    def on_message(self, ws, message):
        event = json.loads(message)
        if 'e' in event and event['e'] == 'depthUpdate':
            # Проверка условий для обработки события
            if not self.last_update_id:
                self.__initialize_order_book()

            if event['u'] <= self.last_update_id:
                return  # Пропускаем событие, если оно устарело

            # Проверка последовательности обновлений
            if 'pu' in event and event['pu'] != self.last_update_id:
                self.__initialize_order_book()
                return

            self.last_update_id = event['u']

            # Обновление книги ордеров
            data = {'bid': event['b'], 'ask': event['a']}
            self.__update_orderbook(data)

    # Обработка ошибок WebSocket
    def on_error(self, ws, error):
        self.alert(error)

    # Обработка закрытия соединения WebSocket
    def on_close(self, ws, close_status_code, close_msg):
        self.alert(f"WebSocket connection closed with code: {close_status_code}, message: {close_msg}")
        time.sleep(300)

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

    def __initialize_order_book(self):
        """ Инициализация книги ордеров с использованием снимка """
        self.last_update_id, combined_data = self.__get_depth_snapshot()
        self.is_first_event_processed = False

        # вставка данных в таблицу
        with self.engine.connect() as conn:
            try:
                conn.execute(self.table.insert(), combined_data)
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.alert('>>>Произошла ошибка при инициализация книги ордеров:<<<\n{}'.format(e))

    def __get_depth_snapshot(self, limit=1000):
        """ Получение снимка книги ордеров """
        url = f"https://fapi.binance.com/fapi/v1/depth?symbol={self.symbol}&limit={limit}"
        response = requests.get(url)
        data = response.json()

        # Очистка таблицы
        with self.engine.connect() as conn:
            try:
                conn.execute(self.table.delete())
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.alert('>>>Произошла ошибка при получении снимка книги ордеров:<<<\n{}'.format(e))

        # Собираем данные предложений (bids) и запросов (asks) в один список
        combined_data = []
        for bid in data["bids"]:
            price, quantity = bid
            combined_data.append({'order_type': 'bid', 'price': float(price), 'quantity': float(quantity)})

        for ask in data["asks"]:
            price, quantity = ask
            combined_data.append({'order_type': 'ask', 'price': float(price), 'quantity': float(quantity)})

        return data["lastUpdateId"], combined_data

    def __update_orderbook(self, data):
        """ Обновление книги ордеров """
        to_delete = []
        to_upsert = []

        for name, array in data.items():
            for row in array:
                price, qty = row
                # Удаление уровня цены, если объем равен нулю
                if float(qty) == 0:
                    to_delete.append((name, price))
                else:
                    to_upsert.append((name, price, qty))

        with self.engine.connect() as conn:
            try:
                # Пакетное удаление
                if to_delete:
                    delete_stmt = delete(self.table).where(
                        tuple_(self.table.c.order_type, self.table.c.price).in_(to_delete)
                    )
                    conn.execute(delete_stmt)

                # Пакетная вставка или обновление
                if to_upsert:
                    insert_stmt = insert(self.table).values([
                        {'order_type': name, 'price': price, 'quantity': qty} for name, price, qty in to_upsert
                    ])
                    on_conflict_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=['order_type', 'price'],
                        set_={'quantity': insert_stmt.excluded.quantity}
                    )
                    conn.execute(on_conflict_stmt)

                conn.commit()
            except Exception as e:
                conn.rollback()
                self.alert('>>>Произошла ошибка при обновлении книги ордеров:<<<\n{}'.format(e))

    # Отправка уведомлений через Telegram
    def alert(self, data):
        bot = telebot.TeleBot(self.token)
        bot.send_message(text='*Received data from Orderbook:*\n\n{}'.format(data),
                         chat_id=self.chat_id, parse_mode='Markdown')


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Параметры подключения к БД
    # DATABASE = os.environ.get('DATABASE')
    # USER = os.environ.get('USER')
    # PASSWORD = os.environ.get('PASSWORD')
    # HOST = os.environ.get('HOST')
    # PORT = os.environ.get('PORT')

    # Строка подключения
    db_url = os.environ.get('POSTGRES')

    # Подключение к базе данных
    engine = create_engine(db_url)

    # Определение таблицы order_book
    metadata = MetaData()
    order_book_table = Table('order_book', metadata,
                             Column('order_type', String, primary_key=True),
                             Column('price', Float, primary_key=True),
                             Column('quantity', Float))

    # Настраиваем Telegram Alert
    token = os.environ.get('TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    symbol = os.environ.get('SYMBOL')
    ws_client = Orderbook(
        url_ws='wss://fstream.binance.com/ws',
        stream_name=['{}@depth'.format(symbol)],
        table=order_book_table,
        engine_=engine,
        token_=token,
        chat_id_=chat_id,
        symbol_=symbol
    )

    # Запуск Websocket
    ws_client.run()

import requests
from sqlalchemy import create_engine
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from clickhouse_driver import Client
import numpy as np
import telebot


class RequestInterfaceSQL:
    def __init__(self, DBMS):
        # Инициализация экземпляра класса
        self.dbms = DBMS
        self.token = os.environ.get('TOKEN')
        self.chat_id = os.environ.get('CHAT_ID')

        if self.dbms == 'clickhouse':
            # Инициализация клиента ClickHouse
            self.clickhouse = Client(host=os.environ.get('HOST'), port='9000', user=os.environ.get('USER'),
                                     password=os.environ.get('PASSWORD'), database=os.environ.get('DATABASE'))
        else:
            # Инициализация движка SQLAlchemy для PostgreSQL
            self.url = os.environ.get('POSTGRES')
            self.postgres = create_engine(self.url)

    def request(self, query):
        # Метод для выполнения запроса к выбранной СУБД
        if self.dbms == 'clickhouse':
            try:
                # Выполнение запроса к ClickHouse
                result = self.clickhouse.execute(query, with_column_types=True)
                # Преобразование результатов в DataFrame
                df = pd.DataFrame(result[0], columns=[col[0] for col in result[1]])
            except Exception as e:
                # Обработка исключения
                self.__alert(f"*backendApp*: ошибка при запросе к ClickHouse:\n{e}")
                df = None
        else:
            try:
                # Выполнение запроса к PostgreSQL и преобразование результатов в DataFrame
                df = pd.read_sql(query, self.postgres)
            except Exception as e:
                # Обработка исключения
                self.__alert(f"*backendApp*: ошибка при запросе к PostgreSQL:\n{e}")
                df = None

        return df

    def __alert(self, message):
        # Инициализация Telegram бота
        bot = telebot.TeleBot(self.token)
        # Отправка сообщения в Telegram чат
        bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')


def get_orderbook_metrics(metric_name, order_range=0.3, price_step=1000):
    # Инициализация соединения с базой данных PostgreSQL
    sql = RequestInterfaceSQL('postgres')

    # Извлечение метрики "spread" (разница между минимальной ценой предложения и максимальной ценой спроса)
    if metric_name == 'spread':
        # Формирование и выполнение SQL-запроса для расчёта spread
        query = """
            SELECT  lowest_ask,
                    highest_bid,
                    lowest_ask - highest_bid AS spread
            FROM    (
                    SELECT
                        MIN(CASE WHEN order_type = 'ask' THEN price END) AS lowest_ask,
                        MAX(CASE WHEN order_type = 'bid' THEN price END) AS highest_bid
                    FROM
                        order_book
                    );
        """
        # Выполнение запроса и возвращение результатов
        spread = sql.request(query)
        return spread

    # Извлечение метрики "ratio" (отношение общего количества спроса к общему количеству предложения)
    elif metric_name == 'ratio':
        # Формирование и выполнение SQL-запроса для расчёта bid_ask_ratio
        query = """
            SELECT
                total_bids,
                total_asks,
                ROUND(total_bids / total_asks, 2) AS bid_ask_ratio
            FROM
                (SELECT SUM(CASE WHEN order_type = 'bid' THEN quantity END) AS total_bids,
                        SUM(CASE WHEN order_type = 'ask' THEN quantity END) AS total_asks
                FROM    order_book);
        """
        # Выполнение запроса и возвращение результатов
        ratio = sql.request(query)
        return ratio

    # Извлечение распределения заявок по ценовым уровням в заданном диапазоне от минимальной цены предложения
    else:
        # Формирование и выполнение SQL-запроса для получения распределения заявок
        query = f"""
            WITH min_ask_price AS (
                SELECT MIN(price) AS min_price
                FROM order_book
                WHERE order_type = 'ask'
            )
            
            SELECT  order_type,
                    ROUND(price / {price_step}) * {price_step} AS price_level,
                    SUM(quantity) AS total_quantity
            FROM    order_book, min_ask_price
            WHERE   price <= (min_ask_price.min_price + min_ask_price.min_price * {order_range})
            AND     price >= (min_ask_price.min_price - min_ask_price.min_price * {order_range})
            GROUP BY
                    order_type,
                    price_level
        """
        # Выполнение запроса и возвращение результатов
        dist = sql.request(query)
        return dist


def current_price():
    # URL эндпоинта Binance Futures API для получения информации о цене
    url = "https://fapi.binance.com/fapi/v2/ticker/price"
    # Параметры запроса: выбор символа торговой пары
    params = {
        "symbol": "BTCUSDT"
    }
    # Выполнение GET запроса к API с указанными параметрами
    response = requests.get(url, params=params)
    # Преобразование ответа из формата JSON в словарь Python
    data = response.json()
    # Создание DataFrame из полученных данных
    price = pd.DataFrame([data])
    # Возвращение DataFrame с текущей ценой
    return price


def kline_to_df(data_):
    # Определение столбцов для DataFrame на основе стандартного формата данных kline
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_Time', 'quote_asset_volume',
               'count', 'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']
    # Создание DataFrame с указанными столбцами
    df_ = pd.DataFrame(data_, columns=columns)

    # Преобразование временных меток из миллисекунд в формат datetime и установка open_time в качестве индекса DataFrame
    df_['open_time'] = pd.to_datetime(df_['open_time'], unit='ms')
    df_['close_Time'] = pd.to_datetime(df_['close_Time'], unit='ms')
    df_.set_index('open_time', inplace=True)

    # Приведение данных к числовому типу
    numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume', 'count',
                       'taker_buy_volume', 'taker_buy_quote_volume']
    df_[numeric_columns] = df_[numeric_columns].astype(float)

    # Расчет дельты как разницы между объемом покупок и продаж
    df_['delta'] = df_['taker_buy_volume'] - (df_['volume'] - df_['taker_buy_volume'])

    # Расчет кумулятивной дельты для анализа общего баланса покупок и продаж
    df_['cumulative_delta'] = df_['delta'].cumsum()

    return df_


def get_kline(symbol_, interval_, days, api, type_):
    # Словарь API URL различных торговых платформ
    apis = {'Binance Futures': 'https://fapi.binance.com/fapi/v1/klines'}
    # Выбор URL API в зависимости от указанного api
    api_url = apis[api]

    # Параметры запроса
    symbol = symbol_
    interval = interval_

    if type_ == 'dashboard':
        # Параметры запроса для дашборда
        params = {
            'symbol': symbol,
            'interval': interval_,
            'limit': days + 1  # Количество дней + 1 для расчета изменения
        }
        # Выполнение запроса и получение данных
        response = requests.get(api_url, params=params)
        data = response.json()

        # Создание DataFrame из полученных данных
        kline = kline_to_df(data)
        # Расчет процентного изменения закрытия и округление до 2 знаков после запятой
        kline['pct_change'] = np.round(kline['close'].pct_change().dropna() * 100, 2)
        kline.dropna(inplace=True, axis=0)

        return kline

    else:
        # Вычисление временных меток для запроса исторических данных
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        start_time_ms = int(start_date.timestamp() * 1000)
        end_time_ms = int(end_date.timestamp() * 1000)

        # Параметры запроса для получения исторических данных
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time_ms,
            'endTime': end_time_ms,
            'limit': 1500  # Максимальное количество свечей в одном запросе
        }

        # Выполнение запроса и получение данных
        response = requests.get(api_url, params=params)
        data = response.json()

        # Создание DataFrame из полученных данных
        kline = kline_to_df(data)

        return kline


def get_funding():
    # URL для запроса данных о финансировании
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    # Параметры запроса: символ торговой пары и лимит количества записей
    params = {
        "symbol": "BTCUSDT",
        "limit": 7 * 3  # получение данных за неделю (3 финансирований в день)
    }
    # Выполнение GET-запроса к API для получения данных
    response = requests.get(url, params=params)
    data = response.json()

    # Создание DataFrame из полученных данных
    funding_rate = pd.DataFrame(data)

    # Преобразование данных
    funding_rate['fundingTime'] = pd.to_datetime(funding_rate['fundingTime'], unit='ms')
    funding_rate['fundingRate'] = funding_rate['fundingRate'].astype(float)
    funding_rate['fundingRate'] = funding_rate['fundingRate'].mul(100)
    funding_rate['markPrice'] = funding_rate['markPrice'].astype(float)

    return funding_rate


def get_oi():
    # URL API для получения данных об открытом интересе
    url = 'https://fapi.binance.com/futures/data/openInterestHist'

    # Параметры запроса: символ торговой пары, период и лимит записей
    params = {
        "symbol": "BTCUSDT",
        'period': '1d',
        'limit': 8
    }

    # Выполнение GET-запроса к API и получение данных
    response = requests.get(url, params=params)
    data = response.json()

    # Создание DataFrame из полученных данных
    open_interest = pd.DataFrame(data)

    # Преобразование данных
    open_interest['timestamp'] = pd.to_datetime(open_interest['timestamp'], unit='ms')
    open_interest['sumOpenInterest'] = open_interest['sumOpenInterest'].astype(float)
    open_interest['sumOpenInterestValue'] = open_interest['sumOpenInterestValue'].astype(float)

    return open_interest


def get_ratio(type_ratio):
    # Выбор URL в зависимости от типа запрашиваемых данных
    if type_ratio == 'global':
        url = 'https://fapi.binance.com/futures/data/globalLongShortAccountRatio'
    else:
        url = 'https://fapi.binance.com/futures/data/topLongShortPositionRatio'

    # Параметры запроса: символ торговой пары, период и количество записей
    params = {
        "symbol": "BTCUSDT",
        'period': '1d',
        'limit': 8
    }

    # Выполнение GET-запроса к API и получение данных
    response = requests.get(url, params=params)
    data = response.json()

    # Создание DataFrame из полученных данных
    ratio = pd.DataFrame(data)

    # Преобразование данных
    ratio['timestamp'] = pd.to_datetime(ratio['timestamp'], unit='ms')
    ratio['longAccount'] = pd.to_numeric(ratio['longAccount'])
    ratio['longShortRatio'] = pd.to_numeric(ratio['longShortRatio'])
    ratio['shortAccount'] = pd.to_numeric(ratio['shortAccount'])

    return ratio


def get_liquidation_metrics(days, metric_name):
    # Инициализация соединения с ClickHouse
    sql = RequestInterfaceSQL('clickhouse')

    # Получение общего объема ликвидаций за последние 7 дней
    if metric_name == 'total_volume':
        query = """
            SELECT  CAST(trade_time AS date) AS trade_date,
                    SUM(quantity) AS total_quantity
            FROM    cryptofinance.liquidation
            WHERE   trade_time >= toDate(NOW()) - INTERVAL 7 DAY
            GROUP BY
                    trade_date
            ORDER BY
                    trade_date
        """
        # Выполнение запроса и возврат результата
        total_volume = sql.request(query)
        return total_volume

    # Получение соотношения ликвидаций по сторонам сделок (покупка/продажа) за последние 7 дней
    elif metric_name == 'ratio':
        query = """
            SELECT
                trade_date,
                SELL_liq,
                BUY_liq,
                ROUND(BUY_liq / NULLIF(SELL_liq, 0), 2) AS ratio
            FROM
                (
                SELECT  
                    trade_date,
                    SUM(CASE WHEN side = 'SELL' THEN total_quantity END) AS SELL_liq,
                    SUM(CASE WHEN side = 'BUY' THEN total_quantity END) AS BUY_liq
                FROM    
                    (
                    SELECT  
                        CAST(trade_time AS date) AS trade_date,
                        side,
                        SUM(quantity) AS total_quantity
                    FROM    
                        cryptofinance.liquidation
                    WHERE
                        trade_time >= toDate(NOW()) - INTERVAL 7 DAY 
                    GROUP BY
                        trade_date,
                        side
                    )
                GROUP BY
                    trade_date
                )
            ORDER BY
                trade_date
        """
        # Выполнение запроса и возврат результата
        ratio = sql.request(query)
        return ratio

    # Получение распределения объема ликвидаций по ценовым уровням за указанное количество дней
    elif metric_name == 'dist':
        query = f"""
            SELECT  FLOOR(price / 100) * 100 AS price_round,
                    SUM(quantity) AS volume
            FROM    cryptofinance.liquidation
            WHERE   trade_time >= toDate(NOW()) - INTERVAL {days - 1} DAY 
            GROUP BY
                    price_round
            HAVING  volume > 1
            ORDER BY
                    price_round
        """
        # Выполнение запроса и возврат результата
        dist = sql.request(query)
        return dist


def get_trades_metrics(agg_func, metric_name, days=7):
    # Инициализация соединения с ClickHouse
    sql = RequestInterfaceSQL('clickhouse')

    # Метрика: Объем торгов
    if metric_name == 'volume':
        # Получение следующего часа для фильтрации данных
        hour = int(datetime.now(timezone.utc).strftime('%H')) + 1

        # Формирование запроса на получение среднего и текущего объема
        query = f"""
            SELECT
                (SELECT
                    toFloat64(AVG(volume)) as average
                FROM
                    (SELECT toDate(trade_time) as trade_date,
                            {agg_func}(quantity) AS volume
                    FROM    cryptofinance.agg_trades
                    WHERE   trade_time >= toDate(NOW()) - INTERVAL 7 DAY
                            AND
                            trade_time < toDate(NOW())
                            AND
                            toHour(trade_time) < {hour}
                    GROUP BY
                            trade_date
                    ORDER BY
                            trade_date)) AS average,
                            
                (SELECT  toFloat64({agg_func}(quantity)) AS volume
                FROM    cryptofinance.agg_trades
                WHERE   trade_time >= toDate(NOW())) AS volume
        """
        # Выполнение запроса и возврат результата
        volume = sql.request(query)
        return volume

    # Метрика: Соотношение покупок к продажам и их процентные доли
    if metric_name == 'ratio':
        query = f"""
            SELECT  trade_date,
                    ROUND(volume_buy / volume_sell, 2) AS buy_sell_ratio,
                    ROUND(volume_buy / (volume_buy + volume_sell) * 100, 2) AS percentage_buy,
                    ROUND(volume_sell / (volume_buy + volume_sell) * 100, 2) AS percentage_sell
            FROM    (
                    SELECT  toDate(trade_time) AS trade_date,
                            {agg_func}(CASE WHEN is_bid = 1 THEN quantity END) AS volume_sell,
                            {agg_func}(CASE WHEN is_bid = 0 THEN quantity END) AS volume_buy
                    FROM    cryptofinance.agg_trades
                    WHERE   trade_time >= toDate(NOW()) - INTERVAL 7 DAY
                    GROUP BY
                            trade_date
            )
        """
        # Выполнение запроса и возврат результата
        ratio = sql.request(query)
        return ratio

    # Метрика: Дельта покупок и продаж
    elif metric_name == 'delta':
        query = f"""
            SELECT  trade_date,
                    volume_buy - volume_sell AS delta
            FROM    (
                    SELECT  toDate(trade_time) AS trade_date,
                            SUM(CASE WHEN is_bid = 1 THEN quantity ELSE 0 END) AS volume_sell,
                            SUM(CASE WHEN is_bid = 0 THEN quantity ELSE 0 END) AS volume_buy
                    FROM    cryptofinance.agg_trades
                    WHERE   trade_time >= toDate(NOW()) - INTERVAL 7 DAY
                    GROUP BY
                            trade_date
            )
        """
        # Выполнение запроса и возврат результата
        delta = sql.request(query)
        return delta

    # Метрика: Распределение объема торгов по ценовым уровням
    elif metric_name == 'dist':
        query = f"""
            SELECT  ROUND(price / 100) * 100 AS price_round,
                    {agg_func}(quantity) AS volume
            FROM    cryptofinance.agg_trades
            WHERE   trade_time >= toDate(NOW()) - INTERVAL {days} DAY
            GROUP BY
                    price_round
        """
        # Выполнение запроса и возврат результата
        dist = sql.request(query)
        return dist


def cluster_search(type_, filter_, timeframe_, symbol_, market, date_start=None, df_=None):
    # Определение квантилей для фильтрации значимых данных
    quantiles = {
        0: 0.95, 1: 0.96, 2: 0.97, 3: 0.98, 4: 0.99
    }
    # Выбор квантиля на основе переданного фильтра
    quantile = quantiles[filter_]

    # Если передан DataFrame, работаем с ним
    if df_ is not None:
        # Словарь соответствия типа анализируемой метрики и столбца в DataFrame
        type_list = {
            'Объём (candle)': 'volume',
            'Кол-во сделок (candle)': 'count',
            'Дельта (candle)': 'delta'
        }
        variable = type_list[type_]

        # Создание маски для выделения значимых значений
        mask = df_[variable].abs() > df_[variable].abs().quantile(quantile)
        # Индексы значимых значений
        highlight_ = df_.loc[mask, variable].index.to_list()

        return highlight_

    # Если DataFrame не передан, выполняем запрос к ClickHouse
    else:
        sql = RequestInterfaceSQL('clickhouse')

        # Словари для агрегации данных и управления временными интервалами
        type_list = {
            'Объём (price)': 'SUM',
            'Кол-во сделок (price)': 'COUNT',
            'Дельта (price)': 'SUM'
        }
        timeframe_list = {
            '1h': 'toStartOfInterval(trade_time, INTERVAL 1 hour)',
            '2h': 'toStartOfInterval(trade_time, INTERVAL 2 hour)',
            '4h': 'toStartOfInterval(trade_time, INTERVAL 4 hour)',
            '1d': 'toStartOfInterval(trade_time, INTERVAL 24 hour)'
        }

        get_timeframe = timeframe_list[timeframe_]
        agg_func = type_list[type_]
        table_sql = 'cryptofinance.agg_trades'

        # Формирование и выполнение SQL-запроса в зависимости от типа анализа
        if type_.split()[0] in ('Объём', 'Кол-во'):
            # Запрос для анализа объёма или количества сделок
            query = f"""
                SELECT
                    timeframe, price, quantity
                FROM
                    (SELECT timeframe, price_round AS price, quantity,
                            MAX(quantity) OVER(PARTITION BY timeframe) AS quantity_max
                    FROM
                            (SELECT
                                {get_timeframe} AS timeframe,
                                FLOOR(price) AS price_round,
                                {agg_func}(quantity) AS quantity
                            FROM 
                                {table_sql}
                            WHERE
                                trade_time >= '{date_start}'
                                AND
                                symbol = '{symbol_}'
                            GROUP BY
                                timeframe, price_round) AS L1) AS L2
                WHERE
                    quantity = quantity_max
            """

            df_ = sql.request(query)
            # Фильтрация и выделение значимых данных
            mask = df_['quantity'].astype(float) > df_['quantity'].astype(float).quantile(quantile)
            markers = df_[mask]

        else:
            # Запрос для анализа дельты
            query = f"""
                SELECT  timeframe, price, quantity_ask, quantity_bid, delta, delta_abs
                FROM    (
                        SELECT
                            timeframe,
                            price_round AS price,
                            quantity_ask,
                            quantity_bid,
                            COALESCE(quantity_ask, 0) - COALESCE(quantity_bid, 0) AS delta,
                            ABS(COALESCE(quantity_ask, 0) - COALESCE(quantity_bid, 0)) AS delta_abs,
                            MAX(ABS(COALESCE(quantity_ask, 0) - COALESCE(quantity_bid, 0))) OVER(PARTITION BY timeframe) AS delta_max
                        FROM 
                            (SELECT
                                {get_timeframe} AS timeframe,
                                FLOOR(price) AS price_round,
                                {agg_func}(CASE WHEN is_bid = false THEN quantity ELSE 0 END) AS quantity_ask,
                                {agg_func}(CASE WHEN is_bid = true THEN quantity ELSE 0 END) AS quantity_bid
                            FROM
                                {table_sql}
                            WHERE
                                trade_time >= '{date_start}'
                                AND
                                symbol = '{symbol_}'
                            GROUP BY
                                timeframe, price_round) AS L1
                        ) L2
                WHERE   delta_abs = delta_max
            """

            df_ = sql.request(query)
            mask = df_['delta_abs'].astype(float) > df_['delta_abs'].astype(float).quantile(quantile)
            markers = df_[mask]

        # Возвращаем временные рамки и цены значимых кластеров
        return markers['timeframe'].values, markers['price'].values

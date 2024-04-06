import os
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import deepl
import telebot
from sqlalchemy import (
    create_engine, Date, Table, select,
    Column, String, MetaData, TEXT, Boolean
)


class CoinDesk:
    def __init__(self, token, chat_id, engine, translator, table):
        self.token = token
        self.chat_id = chat_id
        self.domain = 'https://www.coindesk.com'
        self.engine = engine
        self.translator = translator
        self.table = table

    def get_list_articles(self):
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                           ' Chrome/58.0.3029.110 Safari/537.3')
        }
        response = requests.get('https://www.coindesk.com/livewire/', headers=headers)

        if response.ok:
            # объект BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск блока, который содержит строку "Today"
            today_date_block = soup.find('div', class_="group__TimelineGroupdHeader-sc-ts6p1z-2 emJmAY", string="Today")

            if today_date_block:
                # Поиск родительского элемента, содержащий статьи
                articles_block = today_date_block.find_parent(
                    'div', class_='group__TimelineGroupWrapper-sc-ts6p1z-0 cvQgHz'
                )

                # Статьи внутри блока
                articles = articles_block.find_all(
                    'div', class_="side-cover-cardstyles__SideCoverCardWrapper-sc-1nd3s5z-0 hKtOz side-cover-card"
                )

                # Извлечение информации
                for head in articles:
                    title = head.find('h4').text.strip()
                    link = head.find('a')['href']
                    description = head.find('p').text.strip()
                    date = head.find('span', class_='typography__StyledTypography-sc-owin6q-0 iOUkmj').text.strip()

                    if not self.__query_select(link):
                        url = self.domain + link
                        article = self.__gpt(url)

                        title = self.translator.translate_text(title, target_lang="RU").text
                        description = self.translator.translate_text(description, target_lang="RU").text

                        article_data = {
                            "title": title,
                            "link": link,
                            "description": description,
                            "date": date,
                            'article': article,
                            'source': 'CoinDesk'
                        }

                        self.__query_insert(article_data)
            else:
                check_class = soup.find('div', class_="group__TimelineGroupdHeader-sc-ts6p1z-2 emJmAY")
                if not check_class:
                    self.__alert('*getNews*: проблемы с поиском блока "Today"')

    def __query_select(self, link):
        # Выполнение запроса для проверки наличия статьи в таблице articles
        with self.engine.connect() as conn:
            try:
                query = conn.execute(select(self.table).where(self.table.c.link == link))
                row = query.fetchone()

                return row
            except Exception as e:
                self.__alert('*CoinDesk:* ошибка при запросе SELECT\n{}'.format(e))
                raise

    def __query_insert(self, data):
        # Выполнение запроса для инъекции
        with self.engine.begin() as conn:
            try:
                conn.execute(self.table.insert(), data)
            except Exception as e:
                self.__alert('*CoinDesk:* ошибка при запросе INSERT\n{}'.format(e))
                raise

    def __get_article(self, url):
        # Установка заголовка User-Agent для имитации запроса от браузера
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                           ' Chrome/58.0.3029.110 Safari/537.3')
        }
        # Выполнение GET-запроса к указанному URL с установленными заголовками
        response = requests.get(url, headers=headers)

        if response.ok:
            # Парсинг полученной HTML-страницы
            soup = BeautifulSoup(response.text, 'html.parser')
            # Поиск контейнера с содержимым статьи по классу
            content = soup.find('div', class_="main-body-grid false")

            if content:
                # Поиск всех блоков текста статьи по классу
                text = content.find_all('div', class_='common-textstyles__StyledWrapper-sc-18pd49k-0 eSbCkN')

                article = []
                for row in text:
                    # Добавление текста абзаца в список
                    article.append(row.find('p').text.strip())

                return ' '.join(article)
            else:
                self.__alert(f"*CoinDesk:* проблема с поиском блока 'at-content-wrapper false'\n\nURL: {url}")
        else:
            self.__alert(f'*CoinDesk:* проблема с подключением к {url}, код: {response.status_code}')

    def __gpt(self, url):
        article = self.__get_article(url)

        # Создание запроса к модели GPT для генерации краткого содержания и выводов статьи
        chat_completion = client_ai.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": (f"О чем говорится в этой статье:\n'{article}'\n\n"
                                f"Какие выводы можно сделать на основе этой статьи?"
                                f" Подготовь ответ для публикации на русском языке и используя"
                                f" parse_mode Markdown.")
                }
            ],
            model="gpt-3.5-turbo",  # Указание на использование модели GPT-3.5-turbo
        )

        # Возвращение сгенерированного ответа от GPT
        return chat_completion.choices[0].message.content

    def __alert(self, message):
        bot = telebot.TeleBot(self.token)
        bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')


if __name__ == '__main__':
    # Создание экземпляра переводчика DeepL
    translate = deepl.Translator(os.environ.get('DEEPL'))

    engine_sql = create_engine(
        os.environ.get('MY_POSTGRES')
    )
    token_bot = os.environ.get('MY_TELEGRAM')

    client_ai = OpenAI(api_key=os.environ.get('MY_OPENAI'))

    # Создание объекта метаданных
    meta = MetaData()

    # Описание таблицы пользователей
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

    news = CoinDesk(
        token=token_bot,
        chat_id=os.environ.get('MY_ID'),
        engine=engine_sql,
        translator=translate,
        table=articles_table
    )

    news.get_list_articles()

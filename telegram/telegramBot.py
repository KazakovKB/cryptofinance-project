import os
import logging
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, CallbackQueryHandler, CallbackContext
)
from sqlalchemy import (
    MetaData, Table, Column, SMALLINT,
    BigInteger, String, Boolean, select, Date,
    TIMESTAMP, TEXT, ForeignKey, ForeignKeyConstraint
)


async def fetch_openai_response(question: str, chat_history: list) -> str:
    # Добавляем последний вопрос пользователя к истории диалога
    chat_history.append({"role": "user", "content": question})

    response = await client_ai.chat.completions.create(
        messages=chat_history,
        model="gpt-3.5-turbo",
    )

    # Добавляем ответ GPT к истории диалога
    chat_history.append({"role": "assistant", "content": response.choices[0].message.content})

    return response.choices[0].message.content


# Асинхронная функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Асинхронное подключение к базе данных для проверки наличия пользователя
    async with engine.connect() as conn:
        result = await conn.execute(select(users_table).where(users_table.c.user_id == user.id))
        row = result.fetchone()

    # Если пользователь не найден, добавляем его в базу данных
    if not row:
        # Словарь с данными пользователя для вставки в таблицу
        user_data = {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_premium": user.is_premium,
            "language_code": user.language_code,
            "username": user.username,
            "is_bot": user.is_bot
        }

        # Асинхронное добавление нового пользователя в базу данных
        async with engine.begin() as conn:
            await conn.execute(
                users_table.insert(), user_data
            )

        # Сообщение, отправляемое новому пользователю
        welcome_message = (
            f"*{user.first_name}, приветствую тебя в Telegram боте для анализа данных криптовалютного рынка!* 🚀\n\n"
            "Я здесь, чтобы помочь тебе получить актуальную информацию о криптовалютах, анализировать их динамику и "
            "принимать информированные решения. Просто задавай свои вопросы или запросы, и я постараюсь предоставить "
            "тебе всю необходимую информацию."
        )

    else:
        # Сообщение, отправляемое существующему пользователю
        welcome_message = f"Привет, {user.first_name}! Как я могу помочь тебе сегодня?"

    # Создание клавиатуры с кнопками
    keyboard = [
        [InlineKeyboardButton("👀", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("Скрыть", callback_data='delete_message')]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    # Отправка приветственного сообщения
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, parse_mode='Markdown')

    # Отправка сообщения с предложением перейти к Dashboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="*Перейти к Dashboard:*👇", parse_mode='Markdown', reply_markup=markup
    )


# Асинхронная функция для обработки команды /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    about_bot = ("▪️*Бот-ассистент для трейдеров и аналитиков криптовалютного рынка*\n\n"
                 "*◽️ Веб-приложение с Dashboard'ом*\n\nБот интегрирован с веб-приложением, обладающим мощным и"
                 " интуитивно понятным Dashboard'ом. Этот инструмент позволяет отслеживать "
                 "и анализировать динамику широкого спектра метрик, таких как Delta, Volume, Funding Rate, "
                 "Liquidation и другие. Это предоставляет трейдерам и аналитикам все необходимые данные для"
                 " принятия обоснованных решений, повышая их шансы на успех на быстро меняющемся криптовалютном рынке."
                 "\n\n*◽️ Искусственный интеллект на базе GPT-3.5-turbo*\n\nСердцем бота является искусственный "
                 "интеллект, работающий на основе GPT gpt-3.5-turbo. Это обеспечивает боту возможность не "
                 "только анализировать большие объемы данных в реальном времени, но и предоставлять предсказания, "
                 "аналитические заключения и персонализированные советы. ИИ способен понимать и обрабатывать сложные "
                 "запросы, делая анализ рынка более доступным и менее времязатратным.\n\n"
                 "*◽️ Оперативная доставка новостей и аналитических заключений*\n\nБот обладает способностью мгновенно "
                 "присылать пользователю актуальные новости и делать свои аналитические заключения, касающиеся "
                 "криптовалютного рынка. Это позволяет оставаться в курсе последних событий и тенденций,"
                 " что крайне важно в условиях высокой волатильности криптовалют. Основываясь на данных и аналитике, "
                 "предоставляемых ботом, трейдеры и аналитики могут принимать своевременные и обоснованные решения, "
                 "опираясь на самую актуальную информацию.")

    # Создание клавиатуры с кнопками
    keyboard = [
        [InlineKeyboardButton("Скрыть", callback_data='delete_message')]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    # Отправка сообщения с информацией о боте пользователю
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=about_bot, parse_mode='Markdown', reply_markup=markup
    )


# Асинхронная функция для обработки команды /dashboard
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Создание клавиатуры с кнопками
    keyboard = [
        [InlineKeyboardButton("👀", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("Скрыть", callback_data='delete_message')]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    # Отправка сообщения с предложением перейти к Dashboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="*Перейти к Dashboard:*👇", parse_mode='Markdown', reply_markup=markup
    )


# Асинхронная функция для обработки команды /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Раздел в процессе разработки
    message = "Пожалуйста, ожидайте, профиль станет доступен в ближайшее время."

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode='Markdown'
    )


# Асинхронная функция для обработки команды /subscription
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Раздел в процессе разработки
    message = "Пожалуйста, ожидайте, подписка станет доступна в ближайшее время."

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode='Markdown'
    )


# Асинхронная функция для обработки команды /news
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Доступ к временным данным пользователя в текущей сессии
    user_data = context.user_data

    # Создание клавиатуры с кнопками
    keyboard = [
        [InlineKeyboardButton("Подробнее", callback_data='details_news')],
        [InlineKeyboardButton("⏮", callback_data='previous_news'),
         InlineKeyboardButton("⏭", callback_data='next_news')],
        [InlineKeyboardButton("Скрыть", callback_data='delete_message')]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    # Инициализация смещения для первой загрузки новости
    user_data['offset'] = 0
    # Получение данных о новости, используя функцию get_article с текущим смещением
    data = await get_article(offset=user_data['offset'])

    # Проверка наличия данных
    if data:
        # Распаковка полученных данных
        title, description, date, _, _, _ = data
        # Формирование сообщения
        message = f"📰 *{title}*\n\n_{description}_\n\n📆 {date}"

        # Отправка сообщения пользователю с клавиатурой для навигации
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=message, parse_mode='Markdown', reply_markup=markup
        )


# Асинхронная функция для обработки входящих сообщений
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message  # Получение объекта текущего сообщения
    bot_response = None  # Переменная для хранения ответа бота

    # Получаем историю диалога для текущего пользователя, или инициализируем её, если её нет
    chat_history = context.user_data.get('chat_history', [])
    if not chat_history:
        context.user_data['chat_history'] = [
            {
                "role": "system",
                "content": ("Ты ассистент для трейдеров и аналитиков финансового рынка, специализирующийся"
                            " на криптовалютном рынке. Ты можешь отвечать на вопросы, связанные с криптовалютами"
                            " и финансами. Ты должен отвечать максимально лаконично.")
            }
        ]

    # Асинхронное подключение к базе данных для получения лимитов пользователя
    async with engine.connect() as conn:
        # Выполнение запроса на получение лимита и статуса подписки пользователя
        query = await conn.execute(select(users_table.c.gpt_limit, users_table.c.subscription)
                                   .where(users_table.c.user_id == message.chat_id))
        limit, subscription_val = query.fetchone()

    # Проверка статуса подписки пользователя
    if subscription_val:
        # Если подписка активна, получаем ответ от GPT без учёта лимита
        bot_response = await fetch_openai_response(message.text, chat_history)
    else:
        # Если подписки нет, проверяем длину сообщения и оставшийся лимит запросов
        if len(message.text) <= 200:
            if limit > 0:
                # Получаем ответ от GPT, если лимит не исчерпан
                bot_response = await fetch_openai_response(message.text, chat_history)
            else:
                # Отправка предупреждения о достижении лимита
                warning = ('Еженедельный лимит запросов по вашему текущему плану уже достигнут.'
                           'Чтобы продолжить пользоваться нашими услугами без ограничений, '
                           'вы можете перейти на подписку с безлимитным доступом.')

                await update.message.reply_text(warning)
        else:
            # Отправка предупреждения о превышении допустимой длины сообщения
            warning = ('Ваше сообщение превышает максимально допустимую длину, по вашему текущему плану. '
                       'Пожалуйста, сократите ваш вопрос/запрос, чтобы он не превышал 200 символов.')

            await update.message.reply_text(warning)

    # Если получен ответ от GPT, сохраняем данные сообщения и ответа в базу данных
    if bot_response:
        message_data = {
            "message_id": message.message_id,
            "chat_id": message.chat_id,
            "date": message.date,
            "text": message.text,
            'gpt': bot_response
        }

        # Вставка данных сообщения и ответа в базу данных и обновление лимита
        async with engine.begin() as conn:
            await conn.execute(messages_table.insert(), message_data)

            await conn.execute(
                users_table.update().where(users_table.c.user_id == message.chat_id)
                .values(gpt_limit=users_table.c.gpt_limit - 1)
            )

        # Сохраняем обновлённую историю диалога в context.user_data
        context.user_data['chat_history'] = chat_history

        # Отправка ответа
        await update.message.reply_text(bot_response)


# Асинхронная функция для обработки колбэков от нажатия кнопок
async def button_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query  # Получение объекта запроса колбэка
    await query.answer()  # Отправка уведомления о получении колбэка

    user_data = context.user_data  # Доступ к временным данным пользователя
    callback_data = query.data  # Получение данных, переданных в колбэке

    # Обработка нажатия кнопки "Следующая новость"
    if callback_data == 'next_news':
        user_data['offset'] += 1  # Увеличение смещения для выборки следующей новости
        # Получение данных следующей новости
        title, description, date, _, _, _ = await get_article(offset=user_data['offset'])
        # Формирование и отправка сообщения с новостью
        message = f"📰 *{title}*\n\n_{description}_\n\n📆 {date}"
        await query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=query.message.reply_markup)

    # Обработка нажатия кнопки "Предыдущая новость"
    elif callback_data == 'previous_news' and user_data['offset'] > 0:
        user_data['offset'] -= 1  # Уменьшение смещения для выборки предыдущей новости
        # Получение данных предыдущей новости
        title, description, date, _, _, _ = await get_article(offset=user_data['offset'])
        # Формирование и отправка сообщения с новостью
        message = f"📰 *{title}*\n\n_{description}_\n\n📆 {date}"
        await query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=query.message.reply_markup)

    # Обработка нажатия кнопки "Удалить сообщение"
    elif callback_data == 'delete_message':
        await query.message.delete()  # Удаление сообщения

    # Обработка нажатия кнопки "Подробнее о новости"
    elif callback_data == 'details_news':
        # Получение детализированных данных о новости
        title, _, _, article, link, source = await get_article(offset=user_data['offset'])
        # Формирование URL в зависимости от источника новости
        if source == 'CoinDesk':
            url = 'https://www.coindesk.com' + link
        else:
            url = None
        # Создание клавиатуры с кнопками
        keyboard = [
            [InlineKeyboardButton("Назад", callback_data='main_news')],
            [InlineKeyboardButton("Скрыть", callback_data='delete_message')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        # Формирование и отправка сообщения
        message = f"📰 *{title}*\n\n{article}\n\nИсточник: [{source}]({url})"
        await query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=markup)

    # Возврат к основному просмотру новостей
    elif callback_data == 'main_news':
        # Получение данных текущей новости для возврата к основному просмотру
        title, description, date, _, _, _ = await get_article(offset=user_data['offset'])
        message = f"📰 *{title}*\n\n_{description}_\n\n📆 {date}"
        # Создание клавиатуры с кнопками
        keyboard = [
            [InlineKeyboardButton("Подробнее", callback_data='details_news')],
            [InlineKeyboardButton("⏮", callback_data='previous_news'),
             InlineKeyboardButton("⏭", callback_data='next_news')],
            [InlineKeyboardButton("Скрыть", callback_data='delete_message')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        # Обновление текущего сообщения
        await query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=markup)


# Асинхронная функция для получения одной статьи из базы данных
async def get_article(offset: int) -> tuple:
    # Асинхронное подключение к базе данных
    async with engine.connect() as conn:
        # Формирование SQL запроса для выборки данных одной статьи с сортировкой по убыванию даты
        # и применением смещения, заданного аргументом функции
        query = select(articles_table.c.title,
                       articles_table.c.description,
                       articles_table.c.date,
                       articles_table.c.article,
                       articles_table.c.link,
                       articles_table.c.source).order_by(articles_table.c.date.desc()).offset(offset).limit(1)

        # Выполнение запроса
        result = await conn.execute(query)
        # Извлечение записи из результата запроса
        data = result.fetchone()

        # Возврат данных статьи
        return data


if __name__ == '__main__':
    # Конфигурация логирования
    logging.basicConfig(
        level=logging.WARNING,  # Установка уровня логирования
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат логов
        datefmt='%Y-%m-%d %H:%M:%S'  # Формат даты и времени
    )

    # Настройка асинхронного движка базы данных
    engine = create_async_engine(
        os.environ.get('POSTGRES_ASYNC'),  # Получение строки подключения из переменных окружения
        echo=True  # Вывод SQL запросов в консоль
    )

    # Определение метаданных и структуры таблиц базы данных
    meta = MetaData()

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

    messages_table = Table(
        'messages',
        meta,
        Column('message_id', BigInteger, primary_key=True),
        Column('chat_id', BigInteger, ForeignKey('users.user_id')),
        Column('date', TIMESTAMP(timezone=True)),
        Column('text', TEXT),
        Column('gpt', TEXT),
        ForeignKeyConstraint(['chat_id'], ['users.user_id'], name='fk_users')
    )

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

    # Получение URL веб-приложения из переменных окружения
    WEB_APP_URL = os.environ.get('WEB_APP')

    # Создание и настройка приложения Telegram бота
    app = ApplicationBuilder().token(os.environ.get('TELEGRAM')).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("help", about))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("subscription", subscription))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Инициализация клиента для работы с OpenAI
    client_ai = AsyncOpenAI(api_key=os.environ.get('OPENAI'))

    # Запуск бота в режиме опроса
    app.run_polling()

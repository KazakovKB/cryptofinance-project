import os
import logging
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import httpx
import uuid
from sqlalchemy.sql import func
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, CallbackQueryHandler, CallbackContext
)
from sqlalchemy import (
    MetaData, Table, Column, SMALLINT, Integer,
    BigInteger, String, Boolean, select, Date, and_, text,
    TIMESTAMP, TEXT, ForeignKey, ForeignKeyConstraint, Numeric
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
    else:
        # Сообщение, отправляемое существующему пользователю
        welcome_message = f"Привет, {user.first_name}! Как я могу помочь тебе сегодня?"

        # Отправка приветственного сообщения
        await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, parse_mode='Markdown')


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
    user = update.effective_user  # Получение данных активного пользователя

    # Асинхронное подключение к базе данных
    async with engine.connect() as conn:
        # Выполнение SQL запроса для получения настроек пользователя
        query = await conn.execute(select(users_table.c.newsletter, users_table.c.subscription)
                                   .where(users_table.c.user_id == user.id))
        newsletter_var, subscription_var = query.fetchone()  # Извлечение результатов запроса

    # Определение текста подписки в зависимости от статуса пользователя
    subscription_type = "🌟 Подписка: `PRO`" if subscription_var else "⭐️ Подписка: `Free`"
    # Определение статуса рассылки новостей
    newsletter_status = "🔔 Новости: `Вкл\\.`" if newsletter_var else "🔕 Новости: `Выкл\\.`"

    # Форматирование имени пользователя с экранированием специальных символов для Markdown V2
    first_name = (user.first_name.replace('-', '\\-').replace('.', '\\.')
                  .replace('_', '\\_')) if user.first_name else '\\_'
    last_name = (user.last_name.replace('-', '\\-').replace('.', '\\.')
                 .replace('_', '\\_')) if user.last_name else '\\_'

    # Создание клавиатуры с кнопками для управления
    keyboard = [
        [InlineKeyboardButton("⚙️ Подписка", callback_data='subscription_control')],
        [InlineKeyboardButton("⚙️ Новости", callback_data='news_control')],
        [InlineKeyboardButton("💨 Скрыть", callback_data='delete_message')]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    # Сборка сообщения с информацией о пользователе
    message = f"👤 {first_name} {last_name}\n\n{subscription_type}\n\n{newsletter_status}"

    # Получение и отправка фото профиля пользователя, если оно доступно
    photos = await context.bot.get_user_profile_photos(user_id=user.id)
    if photos.photos:
        photo = photos.photos[0][0]  # Выбор последнего фото
        photo_file = await context.bot.get_file(photo.file_id)  # Получение файла фото

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo_file.file_id,
            caption=message,
            parse_mode='MarkdownV2',
            reply_markup=markup
        )
    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo='https://ibb.co/C7XdhDM',
            caption=message,
            parse_mode='MarkdownV2',
            reply_markup=markup
        )


# Асинхронная функция для обработки команды /subscription
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user  # Получение данных активного пользователя

    # Асинхронное подключение к базе данных
    async with engine.connect() as conn:
        # Выполнение SQL запроса для получения информации о наличии действующего заказа
        query_sql = await conn.execute(select(orders_table.c.id).where(
            and_(orders_table.c.user_id == user.id, orders_table.c.status == 'ACTIVE')
        ))
        order_id = query_sql.fetchone()  # Извлечение результатов запроса

        # Выполнение SQL запроса для получения информации о статусе пользователя
        query_sql = await conn.execute(select(users_table.c.subscription).where(users_table.c.user_id == user.id))
        status = query_sql.fetchone()[0]  # Извлечение результатов запроса

    # Если у пользователя активная подписка
    if status:
        async with engine.connect() as conn:
            # Подготовка SQL-запроса для получения информации о сроках действия подписки
            query_sql = (
                select(
                    (orders_table.c.updated_at + text("INTERVAL '30 days'")).label('expires_on'),
                    (orders_table.c.updated_at + text("INTERVAL '30 days'") - func.current_timestamp()).label(
                        'time_left')
                )
                .where(
                    and_(
                        orders_table.c.user_id == user.id,
                        orders_table.c.status == 'PAID'
                    )
                )
                .order_by(orders_table.c.updated_at.desc()).limit(1)
            )

            # Выполнение запроса
            result = await conn.execute(query_sql)
            subscription_info = result.fetchone()  # Извлечение результатов запроса

        # Отправка информации о сроках подписки пользователя
        message = (
            f"*Срок действия подписки истекает:*\n📆 {subscription_info.expires_on.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"*Оставшееся время:*\n⏳ {subscription_info.time_left}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

    # Если у пользователя нет активной подписки, но есть активный заказ
    else:
        if order_id:
            headers = {
                'Wpay-Store-Api-Key': wallet_tg,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            payload = {
                'id': order_id[0]
            }

            # Создание асинхронного HTTP клиента для запроса к API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://pay.wallet.tg/wpay/store-api/v1/order/preview",
                    params=payload, headers=headers, timeout=10
                )
                if response.status_code != 200:
                    data = None
                else:
                    data = response.json()

            # Если получены данные о заказе
            if data:
                if data['data']['status'] == 'EXPIRED':
                    # Обновление статуса заказа
                    async with engine.begin() as conn:
                        await conn.execute(
                            orders_table.update().where(
                                and_(orders_table.c.user_id == user.id, orders_table.c.status == 'ACTIVE')
                            ).values(status='EXPIRED')
                        )
                    # Формирование нового заказа
                    external_id = str(uuid.uuid4())

                    headers = {
                        'Wpay-Store-Api-Key': wallet_tg,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    }

                    payload = {
                        'amount': {
                            'currencyCode': 'TON',
                            'amount': '0.1',
                        },
                        'description': 'Subscription payment',
                        'externalId': f'{external_id}',
                        'timeoutSeconds': 86400,
                        'customerTelegramUserId': f'{user.id}',
                        'returnUrl': 'https://t.me/cryptofinance_project_bot',
                        'failReturnUrl': 'https://t.me/wallet',
                    }

                    # Выполнение POST-запроса для создания нового заказа
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            "https://pay.wallet.tg/wpay/store-api/v1/order",
                            json=payload, headers=headers, timeout=10
                        )
                        if response.status_code != 200:
                            data = None
                        else:
                            data = response.json()

                    # Если заказ успешно создан
                    if data:
                        # Вставка данных о новом заказе в базу данных
                        order_data = {
                            'id': int(data['data']['id']),
                            "external_id": external_id,
                            "order_number": data['data']['number'],
                            "amount": 0.1,
                            "currency_code": 'TON',
                            "description": 'Subscription payment',
                            "status": data['data']['status'],
                            "user_id": user.id
                        }

                        async with engine.begin() as conn:
                            await conn.execute(orders_table.insert(), order_data)

                        # Подготовка ссылки для оплаты и отправка сообщения пользователю с кнопкой для оплаты
                        url = data['data']['payLink']
                        keyboard = [
                            [InlineKeyboardButton("👛 Pay via Wallet", url=url)],
                        ]
                        markup = InlineKeyboardMarkup(keyboard)

                        message = ('*Сменить план на Pro:*\n\n⚠️ После оплаты, для активации, '
                                   'повторно используйте команду: /subscription')
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id, text=message,
                            reply_markup=markup, parse_mode='Markdown'
                        )
                    else:
                        # Отправка сообщения о неудаче при создании заказа
                        message = ("*Что-то пошло не так...* 👀\n\nПожалуйста,"
                                   " повторно используйте команду: /subscription")
                        await context.bot.send_message(chat_id=update.effective_chat.id,
                                                       text=message, parse_mode='Markdown')

                elif data['data']['status'] == 'PAID':
                    # Обновление статуса пользователя и заказа в базе данных после успешной оплаты
                    async with engine.begin() as conn:
                        await conn.execute(
                            users_table.update().where(users_table.c.user_id == user.id).values(
                                subscription=True,
                                subscription_end=func.current_date() + text('INTERVAL \'31 day\'')
                            )
                        )

                        await conn.execute(
                            orders_table.update().where(
                                and_(orders_table.c.user_id == user.id, orders_table.c.status == 'ACTIVE')
                            ).values(status='PAID')
                        )

                    # Отправка сообщения об успешной активации Pro плана
                    message = "*Ваш план изменен на Pro!* 🌟"
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text=message, parse_mode='Markdown'
                    )
                else:
                    # Иначе, отправка сообщения с предложением оплатить по старой ссылке
                    url = data['data']['payLink']

                    keyboard = [
                        [InlineKeyboardButton("👛 Pay via Wallet", url=url)],
                    ]
                    markup = InlineKeyboardMarkup(keyboard)

                    message = ('*Сменить план на Pro:*\n\n⚠️ После оплаты, для активации, '
                               'повторно используйте команду: /subscription')
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text=message,
                        reply_markup=markup, parse_mode='Markdown'
                    )
            else:
                # Отправка сообщения об ошибке, если данные о заказе не получены
                message = ("*Что-то пошло не так...* 👀\n\nПожалуйста,"
                           " повторно используйте команду: /subscription")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')
        else:
            # Если у пользователя нет активного заказа, инициация создания нового заказа
            external_id = str(uuid.uuid4())

            headers = {
                'Wpay-Store-Api-Key': wallet_tg,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            payload = {
                'amount': {
                    'currencyCode': 'TON',
                    'amount': '0.1',
                },
                'description': 'Subscription payment',
                'externalId': f'{external_id}',
                'timeoutSeconds': 86400,
                'customerTelegramUserId': f'{user.id}',
                'returnUrl': 'https://t.me/cryptofinance_project_bot',
                'failReturnUrl': 'https://t.me/wallet',
            }

            # Выполнение POST-запроса для создания нового заказа
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://pay.wallet.tg/wpay/store-api/v1/order",
                    json=payload, headers=headers, timeout=10
                )
                if response.status_code != 200:
                    data = None
                else:
                    data = response.json()
            if data:
                # Вставка данных о новом заказе в базу данных
                order_data = {
                    'id': int(data['data']['id']),
                    "external_id": external_id,
                    "order_number": data['data']['number'],
                    "amount": 0.1,
                    "currency_code": 'TON',
                    "description": 'Subscription payment',
                    "status": data['data']['status'],
                    "user_id": user.id
                }

                async with engine.begin() as conn:
                    await conn.execute(orders_table.insert(), order_data)

                # Подготовка ссылки для оплаты и отправка сообщения пользователю с кнопкой для оплаты
                url = data['data']['payLink']

                keyboard = [
                    [InlineKeyboardButton("👛 Pay via Wallet", url=url)],
                ]
                markup = InlineKeyboardMarkup(keyboard)

                message = ('*Сменить план на Pro:*\n\n⚠️ После оплаты, для активации, '
                           'повторно используйте команду: /subscription')
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=message, reply_markup=markup, parse_mode='Markdown'
                )
            else:
                message = ("*Что-то пошло не так...* 👀\n\nПожалуйста,"
                           " повторно используйте команду: /subscription")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')


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
        await update.message.reply_text(bot_response, parse_mode='Markdown')


# Асинхронная функция для обработки колбэков от нажатия кнопок
async def button_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query  # Получение объекта запроса колбэка

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

    # Обработка нажатия кнопки "Управление новостями"
    elif callback_data == 'news_control':
        message = "⚙️ *Новости:*"
        # Создание клавиатуры с кнопками
        keyboard = [
            [InlineKeyboardButton("📩 Рассылка", callback_data='newsletter_status')],
            [InlineKeyboardButton("🌐 Источники", callback_data='news_source')],
            [InlineKeyboardButton("🔙 Назад", callback_data='profile')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        # Обновление текущего сообщения
        await query.edit_message_caption(caption=message, parse_mode='Markdown', reply_markup=markup)

    # Обработка нажатия кнопки "Вернуться к профилю"
    elif callback_data == 'profile':
        # Удаление сообщения
        await query.message.delete()
        # Вызов функции обработчика команды /profile
        await profile(update, context)

    # Обработка нажатия кнопки "Настройка рассылки"
    elif callback_data == 'newsletter_status':
        # Асинхронное подключение к базе данных
        async with engine.connect() as conn:
            # Выполнение запроса на получение данных
            query_sql = await conn.execute(
                select(users_table.c.newsletter).where(users_table.c.user_id == update.effective_user.id))
            newsletter_var = query_sql.fetchone()

        message = "⚙️ *Рассылка:*"
        status = "🔔 Вкл." if bool(newsletter_var[0]) else "🔕 Выкл."
        # Создание клавиатуры с кнопками
        keyboard = [
            [InlineKeyboardButton(status, callback_data='newsletter_checkout')],
            [InlineKeyboardButton("🔙 Назад", callback_data='profile')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        # Обновление текущего сообщения
        await query.edit_message_caption(caption=message, parse_mode='Markdown', reply_markup=markup)

    # Обработка нажатия кнопки "Изменение настройки рассылки"
    elif callback_data == 'newsletter_checkout':
        # Обновление статуса
        async with engine.begin() as conn:
            await conn.execute(
                users_table.update().where(users_table.c.user_id == update.effective_user.id)
                .values(newsletter=~users_table.c.newsletter)
            )

        # Всплывающее уведомление
        await query.answer('✅\nНастройки рассылки успешно изменены!', show_alert=True)

        # Удаление сообщения
        await query.message.delete()
        # Вызов функции обработчика команды /profile
        await profile(update, context)

    # Обработка нажатия кнопки "Источники новостей"
    elif callback_data == 'news_source':
        # Всплывающее уведомление
        await query.answer('🏗\nПожалуйста, ожидайте, выбор источников новостей станет доступен в ближайшее время.',
                           show_alert=True)

    # Обработка нажатия кнопки "Управление подпиской"
    elif callback_data == 'subscription_control':
        # Удаление сообщения
        await query.message.delete()
        # Вызов функции обработчика команды /subscription
        await subscription(update, context)


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
        Column('subscription', Boolean, default=False),
        Column('subscription_end', Date)
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

    # API для Wallet Telegram
    wallet_tg = os.environ.get('WALLET')

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

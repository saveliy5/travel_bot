import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta
import os


# Получите абсолютный путь к текущей директории
base_dir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(base_dir, 'travel_bot.db')

# Установите токен вашего бота
TOKEN = ''
HOTEL_LINK = 'https://tp.st/TZA2MJW4'
AIRPLANE_LINK = 'https://aviasales.tp.st/C9qeS4te'
TOUR_LINK = 'https://travelata.tp.st/3U2N1QA4'

# Создайте объект бота
bot = telebot.TeleBot(TOKEN)

user_city_selection = {}


# Функция для нормализации названия города
def normalize_city(city):
    # Приводим к одному регистру и делаем первую букву заглавной
    city = city.lower()
    # Заменяем "питер" на "Санкт-Петербург"
    if city in ["питер", "санкт петербург", "санкт питербург"]:
        return "Санкт-Петербург"
    city = city.capitalize()
    return city


# Функция для отправки информации о городе
def send_city_info(message, city):
    normalized_city = normalize_city(city)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT info FROM cities_info WHERE city=?', (normalized_city,))
    info = cursor.fetchone()

    conn.close()

    if info:
        need_message = info[0]
        need_message += '\n\n\U0001F3E8 ' + f'[БРОНИРУЙТЕ ОТЕЛИ ВЫГОДНО ТУТ]({HOTEL_LINK})'
        need_message += '\n\U00002708 ' + f'[ДЕШЕВЫЕ АВИАБИЛЕТЫ ТУТ]({AIRPLANE_LINK})'
        need_message += '\n\U0001F9F3 ' + f'[СРАЗУ ТУР]({TOUR_LINK})'
        bot.send_message(message.chat.id, need_message, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Информации о данном городе нет в базе данных. Попробуйте другой город.")


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Москва")
    item2 = types.KeyboardButton("Питер")
    item3 = types.KeyboardButton("Казань")
    item4 = types.KeyboardButton("Калининград")
    item5 = types.KeyboardButton("Сочи")
    item6 = types.KeyboardButton("Владивосток")
    item7 = types.KeyboardButton("Другой")
    markup.add(item1, item2, item3, item4, item5, item6, item7)

    bot.send_message(message.chat.id, "Выберите город из списка кнопок или отправьте 'Другой', чтобы ввести город вручную.", reply_markup=markup)


# Функция для проверки наличия опасных SQL-команд в запросе
def contains_dangerous_sql(query):
    dangerous_commands = [
        "drop",
        "delete",
        "update",
        "alter",
        "truncate",
        "insert",
        "select",
        "grant",
        "revoke"
    ]
    query = query.lower()
    for command in dangerous_commands:
        if command in query:
            return True
    return False


# Функция для записи лога в базу данных
def log_message(user_id, timestamp, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if contains_dangerous_sql(message):
        message = 'Запрос содержит опасные команды'

    cursor.execute('INSERT INTO message_logs (user_id, timestamp, message) VALUES (?, ?, ?)',
                   (user_id, datetime.utcfromtimestamp(timestamp) + timedelta(hours=3), message))

    conn.commit()
    conn.close()


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    city = message.text

    if city == "Другой":
        bot.send_message(message.chat.id, "Пожалуйста, введите название города вручную.")
    else:
        send_city_info(message, city)
    # Записываем лог в базу данных
    log_message(message.from_user.id, message.date, city)


def main():
    # Запуск бота
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()


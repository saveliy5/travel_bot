import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta
import os
import json


# Получите абсолютный путь к текущей директории
base_dir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(base_dir, 'travel_bot.db')
CONFIG_PATH = os.path.join(base_dir, 'config.json')

# Загрузка конфигурационных данных из файла
with open(CONFIG_PATH, "r") as config_file:
    config_data = json.load(config_file)

# Установите токен вашего бота
TOKEN = config_data['telegram_bot_token']
HOTEL_LINK = config_data['hotel_partner_link']
AIRPLANE_LINK = config_data['airplane_partner_link']
TOUR_LINK = config_data['tour_partner_link']

# Создайте объект бота
bot = telebot.TeleBot(TOKEN)

user_city_selection = {}
count_days_dict = {
    1: ['1', '1 день', 'один', 'один день'],
    2: ['2', '2 дня', 'два', 'два дня'],
    3: ['3', '3 дня', 'три', 'три дня'],
    4: ['4', '4 дня', 'четыре', 'четыре дня'],
}
all_count_days = [item for sublist in count_days_dict.values() for item in sublist]


# Функция для нормализации названия города
def normalize_city(city):
    # Приводим к одному регистру и делаем первую букву заглавной
    city = city.lower()
    # Заменяем "питер" на "Санкт-Петербург"
    if city in ["питер", "санкт петербург", "санкт питербург"]:
        return "Санкт-Петербург"
    city = city.capitalize()
    return city


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


# Функция для отправки информации о городе
def send_city_info(message, city):
    normalized_city = normalize_city(city)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM cities_info WHERE city=?', (normalized_city,))
    info = cursor.fetchone()

    conn.close()

    if info:
        # Город найден, предлагаем выбрать количество дней кнопками
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("1 день")
        item2 = types.KeyboardButton("2 дня")
        item3 = types.KeyboardButton("3 дня")
        item4 = types.KeyboardButton("4 дня")
        item_back = types.KeyboardButton("Назад")
        markup.add(item1, item2, item3, item4, item_back)

        user_city_selection[message.from_user.id]["city"] = normalized_city

        bot.send_message(message.chat.id, "Выберите количество дней:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Информации о данном городе нет в базе данных. Попробуйте другой город.")
        # start(message)
        user_city_selection.pop(message.from_user.id)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in user_city_selection:
        user_city_selection.pop(message.from_user.id)  # Удаляем информацию о выборе пользователя
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


# Обработчик выбора количества дней
@bot.message_handler(func=lambda message: message.text.lower() in all_count_days)
def handle_days_selection(message):
    if message.from_user.id not in user_city_selection:
        bot.send_message(message.chat.id, "Сначала выберите город.")
        # start(message)
        return

    user_data = user_city_selection[message.from_user.id]

    # if user_data["city"] == "":
    #     bot.send_message(message.chat.id, "Сначала выберите город.")
    #     start(message)
    #     return

    need_count_days = '0'
    for key, value_list in count_days_dict.items():
        for value in value_list:
            if value == message.text.lower():
                need_count_days = key

    need_city = user_data["city"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT info FROM cities_info WHERE city=?', (need_city,))
    info = cursor.fetchone()

    conn.close()

    need_message = info[0]
    need_message += f'\n\n Количество дней {need_count_days}'
    need_message += '\n\n\U0001F3E8 ' + f'[БРОНИРУЙТЕ ОТЕЛИ ВЫГОДНО ТУТ]({HOTEL_LINK})'
    need_message += '\n\U00002708 ' + f'[ДЕШЕВЫЕ АВИАБИЛЕТЫ ТУТ]({AIRPLANE_LINK})'
    need_message += '\n\U0001F9F3 ' + f'[СРАЗУ ТУР]({TOUR_LINK})'
    bot.send_message(message.chat.id, need_message, parse_mode='Markdown')

    user_city_selection.pop(message.from_user.id)  # Удаляем информацию о выборе пользователя

    # Затем вернем пользователя к выбору города.
    start(message)


# Обработчик кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "Назад")
def handle_back_button(message):
    if message.from_user.id in user_city_selection:
        user_city_selection.pop(message.from_user.id)  # Удаляем информацию о выборе пользователя
    start(message)  # Возвращаем пользователя к выбору города


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id not in user_city_selection:
        user_city_selection[message.from_user.id] = {"city": "", "days": ""}
    if user_city_selection[message.from_user.id]["city"] != "":
        bot.send_message(message.chat.id, "Выберите другое количество дней или нажмите назад")
        return

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


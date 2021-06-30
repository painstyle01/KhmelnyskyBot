
import datetime
from os import remove
import time
import gspread
import mysql.connector
import telebot
from telebot import types
from geopy.geocoders import Nominatim
from geopy import distance
from apscheduler.schedulers.background import BackgroundScheduler

geolocator = Nominatim(user_agent="painstyle01_telegram_token_bot")
scheduler = BackgroundScheduler()

db = mysql.connector.connect(host='localhost', user='root', password='#', database='tickets')
c = db.cursor(buffered=True)

gc = gspread.service_account(filename='gspread.json')
bot = telebot.TeleBot("#")

db.autocommit = True
db.close()
work = (49.995721, 36.204540)

mk = types.ReplyKeyboardMarkup(True)
mk.row("Выйти на обед")
mk.row("На перекур")
mk.row("Ушел с работы")
mk.row("Я на работе")

mk2 = types.ReplyKeyboardMarkup(True)
mk2.row("Я на рабочем месте")

mk3 = types.ReplyKeyboardMarkup(True)
mk3.row("Я вернулся")

def workFix():
    db.connect()
    c.execute("UPDATE users SET step='main_menu'")
    db.close()

def getLocation():
    db.connect()
    t = time.time()
    print(type(t))
    print(t)
    c.execute("UPDATE debug SET time='{}' WHERE id=1".format(t))
    c.execute("UPDATE users SET step='geo' WHERE step='main_menu'")
    c.execute("SELECT id FROM users WHERE step='geo'")
    data = c.fetchall()
    print(data)
    for users in data:
        try:
            print(users[0])
            bot.send_message(users[0], "Добрый день! Отправьте, пожалуйста, лайв геометку.")
        except:
            pass
    db.close()

def getLocation2():
    db.connect()
    t = time.time()
    print(type(t))
    print(t)
    c.execute("UPDATE debug SET time='{}' WHERE id=1".format(t))
    c.execute("UPDATE users SET step='geo_end' WHERE step='main_menu'")
    c.execute("SELECT id FROM users WHERE step='geo_end'")
    data = c.fetchall()
    print(data)
    for users in data:
        try:
            print(users[0])
            bot.send_message(users[0], "Добрый день! Отправьте, пожалуйста, лайв геометку.")
        except:
            pass
    db.close()

@bot.message_handler(commands=['geom'])
def g(message):
    getLocation()

@bot.message_handler(commands=['smoking'])
def g(message):
    db.connect()
    c.execute("SELECT COUNT(id) FROM users WHERE step='smoking'")
    bot.send_message(message.from_user.id, "На перекуре {} пользователей.".format(c.fetchone()[0]))
    db.close()

@bot.message_handler(commands=['report'])
def g(message):
    db.connect()
    c.execute("SELECT name, surname, step FROM users")
    d = c.fetchall()
    s = ""
    print(d)
    for i in d:
        s += f"{i[0]} {i[1]} - {i[2]}\n"
    bot.send_message(message.from_user.id, s.replace("smoking","На перекуре").replace("geo_end","Жду метку на конец дня").replace("geo_leave","Не на работе").replace("main_menu","На работе").replace("geo_enter", "На обеде, жду метки").replace("name","Регистрация").replace("surname","Регистрация").replace("geo_cc","Отправляет метку").replace("geo_ll","Отправляет метку").replace("geo","Не на работе, жду метку.").replace("reason","Не на работе. Жду причину прогула."))
    db.close()

@bot.message_handler(commands=['start'])
def start_handler(message):
    db.connect()
    c.execute("SELECT step FROM users WHERE id={}".format(message.from_user.id))
    data = c.fetchone()
    print(data)
    if data is None:
        ss = gc.open("Telegram Bot Tickets")
        c.execute("INSERT INTO users(id,step) VALUES ('{}','{}')".format(message.from_user.id, "name"))
        c.execute("INSERT INTO debug(id,time) VALUES ('{}','0')".format(message.from_user.id))
        bot.send_message(message.from_user.id,
                         "Приветствую. Для того что бы я начал обрабатывать вашу геометку, мне нужно её получить.\n"
                         "Ожидайте на запрос геометки\n<b>Ваши метки не будут видны ни разработчику, ни руководству.</b>\nПожалуйста, введите Ваше имя.",
                         parse_mode="HTML")
    else:
        pass
    db.close()

@bot.message_handler(commands=['id'])
def ms(message):
    bot.send_message(message.chat.id, message.chat.id)

@bot.message_handler(content_types=['location'])
def location_save(message):
    db.connect()
    c.execute("SELECT * FROM users WHERE id='{}'".format(message.from_user.id))
    d = c.fetchone()
    name = d[2]
    surname = d[3]
    ss = gc.open("Telegram Bot Tickets")
    works = ss.worksheet("Sheet 1")
    lr = len(works.get_all_values()) + 1
    live_period = message.json.get("location")
    m = live_period.get("live_period")
    if m is None:
        bot.send_message(message.from_user.id, "Мне нужно получить Live геометку.")
    else:
        c.execute('SELECT step FROM users WHERE id="{}"'.format(message.from_user.id))
        dist = distance.distance(work, (message.location.latitude, message.location.longitude)).meters
        print(dist)
        data = c.fetchone()[0]
        if data == "geo_cc":
            print("cc")
            c.execute("SELECT time FROM debug")
            time_elapsed = c.fetchone()
            l = geolocator.reverse("{}, {}".format(message.location.latitude, message.location.longitude))
            print(l.address)
            dist = distance.distance(work, (message.location.latitude, message.location.longitude)).meters
            if dist < 100:
                print("ping")
                bot.send_message(message.from_user.id, "Спасибо. По координатам вы находитесь на работе. Хорошего дня",
                                 reply_markup=mk)
                works.update(f"A{lr}", "Получена геометка. На работе по кнопке")
                c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
                c.execute("UPDATE debug SET time='{}' WHERE id={}".format(time.time(), message.from_user.id))
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "На работе")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
            if dist >= 100:
                print("pong")
                works.update(f"A{lr}", "Получена геометка. Не на работе")
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Не на работе.".format(message.text))
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
                bot.send_message(message.from_user.id, "Геолокация не верна.")
        if data == "geo_ll":
            c.execute("SELECT time FROM debug")
            time_elapsed = c.fetchone()
            l = geolocator.reverse("{}, {}".format(message.location.latitude, message.location.longitude))
            print(l.address)
            dist = distance.distance(work, (message.location.latitude, message.location.longitude)).meters
            if dist < 100:
                bot.send_message(message.from_user.id, "Спасибо. Я вас отметил. Хорошего дня",
                                 reply_markup=mk)
                works.update(f"A{lr}", "Получена геометка. Ушел с работы по кнопке")
                c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
                c.execute("UPDATE debug SET time='{}' WHERE id={}".format(time.time(), message.from_user.id))
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Ушел с работы")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
            if dist >= 100:
                works.update(f"A{lr}", "Получена геометка. Не на работе")
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Не на работе.".format(message.text))
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
                bot.send_message(message.from_user.id, "Геолокация не верна.")
        if data == "geo_end":
            c.execute("SELECT time FROM debug")
            time_elapsed = c.fetchone()
            dist = distance.distance(work, (message.location.latitude, message.location.longitude)).meters
            if dist < 100:
                
                bot.send_message(message.from_user.id, "Спасибо. Рабочий день завершен.",
                                 reply_markup=mk)
                # Action Type	User First Name	User Last Name	Location	Location(address)	On Work	TG ID	Date
                # A1 B1 C1 D1 E1 F1 G1 H1 J1
                works.update(f"A{lr}", "Получена геометка.")
                c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
                c.execute("UPDATE debug SET time='{}' WHERE id={}".format(time.time(), message.from_user.id))
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"F{lr}", "Ушел с работы")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
            if dist >= 100:
                l = geolocator.reverse("{}, {}".format(message.location.latitude, message.location.longitude))
                works.update(f"A{lr}", "Получена геометка. Не на работе")
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Не на работе. Проверка в конце дня.")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
                bot.send_message(message.from_user.id, "Напишите, пожалуйста, причину отсутствия на работе.")
                c.execute("UPDATE users SET step='reason' WHERE id={}".format(message.from_user.id))
        if data == "geo":
            c.execute("SELECT time FROM debug")
            time_elapsed = c.fetchone()
            l = geolocator.reverse("{}, {}".format(message.location.latitude, message.location.longitude))
            print(l.address)
            dist = distance.distance(work, (message.location.latitude, message.location.longitude)).meters
            if dist < 100:
                bot.send_message(message.from_user.id, "Спасибо. По координатам вы находитесь на работе. Хорошего дня",
                                 reply_markup=mk)
                works.update(f"A{lr}", "Получена геометка. На работе")
                c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
                c.execute("UPDATE debug SET time='{}' WHERE id={}".format(time.time(), message.from_user.id))
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Пришел на работу")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
            if dist >= 100:
                works.update(f"A{lr}", "Получена геометка. Не на работе")
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Не на работе.".format(message.text))
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
                bot.send_message(message.from_user.id, "Напишите, пожалуйста, причину отсутствия на работе.")
                c.execute("UPDATE users SET step='reason' WHERE id={}".format(message.from_user.id))
        if data == "geo_leave":
            c.execute("SELECT time FROM debug")
            time_elapsed = c.fetchone()
            l = geolocator.reverse("{}, {}".format(message.location.latitude, message.location.longitude))
            print(l.address)
            if dist < 100:
                bot.send_message(message.from_user.id,
                                 "Спасибо. По координатам вы находитесь на работе. Можете идти на обед. Нажмите на кнопку когда вернетесь.",
                                 reply_markup=mk2)
                works.update(f"A{lr}", "Получена геометка. На работе")

            if dist >= 100:
                works.update(f"A{lr}", "Получена геометка. Не на работе")
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Не на работе. Уход на обед.")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
                bot.send_message(message.from_user.id, "Вы не на работе. Что б начать обед нужно находится в офисе.")
        if data == 'geo_enter':
            c.execute("SELECT time FROM debug")
            time_elapsed = c.fetchone()
            l = geolocator.reverse("{}, {}".format(message.location.latitude, message.location.longitude))
            print(l.address)
            dist = distance.distance(work, (message.location.latitude, message.location.longitude)).meters
            if dist < 100:
                bot.send_message(message.from_user.id,
                                 "Спасибо. По координатам вы находитесь на работе. Хорошего дня.",
                                 reply_markup=mk)
                works.update(f"A{lr}", "Получена геометка. На работе")
            if dist >= 100:
                works.update(f"A{lr}", "Получена геометка. Не на работе")
                works.update(f"B{lr}", name)
                works.update(f"C{lr}", surname)
                works.update(f"D{lr}", "{} {}".format(message.location.latitude, message.location.longitude))
                works.update(f"E{lr}", l.address)
                works.update(f"F{lr}", "Не на работе. Отметка.")
                works.update(f"G{lr}", message.from_user.id)
                t = time.time() - float(time_elapsed[0])
                works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
                bot.send_message(message.from_user.id,
                                 "Вы не на работе. Что б закончить обед нужно находится в офисе.")
    db.close()

@bot.message_handler(content_types=['text'])
def text_handler(message):
    db.connect()
    ss = gc.open("Telegram Bot Tickets")
    works = ss.worksheet("Sheet 1")
    lr = len(works.get_all_values()) + 1
    c.execute("SELECT * FROM users WHERE id='{}'".format(message.from_user.id))
    d = c.fetchone()
    name = d[2]
    surname = d[3]
    c.execute("SELECT step FROM users WHERE id={}".format(message.from_user.id))
    data = c.fetchone()[0]
    if data == "name":
        c.execute("UPDATE users SET name='{}' WHERE id={}".format(message.text, message.from_user.id))
        c.execute("UPDATE users SET step='surname' WHERE id={}".format(message.from_user.id))
        bot.send_message(message.from_user.id, "Введите вашу фамилию.")
    if data == "surname":
        c.execute("UPDATE users SET surname='{}' WHERE id={}".format(message.text, message.from_user.id))
        c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
        bot.send_message(message.from_user.id, "Спасибо. Ожидайте метки.", reply_markup=mk)
    if data == "reason":
        works.update(f"A{lr}", "Причина")
        c.execute("UPDATE users SET step='geo' WHERE id={}".format(message.from_user.id))
        works.update(f"B{lr}", name)
        works.update(f"C{lr}", surname)
        works.update(f"F{lr}", "{}".format(message.text))
        works.update(f"G{lr}", message.from_user.id)
        works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
        bot.send_message(message.from_user.id, "Я это записал. Пожалуйста, отправьте гееометку когда будете на работе.")
        bot.send_message(12312312, "{} {}\nПричина отутствия: {}".format(name,surname,message.text))
    else:
        if message.text == "Ушел с работы":
            c.execute("UPDATE users SET step='geo_ll' WHERE id={}".format(message.from_user.id))
            bot.send_message(message.chat.id, "Отправьте вашу геометку.", reply_markup=types.ReplyKeyboardRemove())
        if message.text == "Я на работе":
            c.execute("UPDATE users SET step='geo_cc' WHERE id={}".format(message.from_user.id))
            bot.send_message(message.chat.id, "Отправьте вашу геометку.", reply_markup=types.ReplyKeyboardRemove())
        if message.text == "Выйти на обед":
            c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
            c.execute("UPDATE debug SET lunch_timestamp='{}' WHERE id={}".format(time.time(), message.from_user.id))
            works.update(f"A{lr}", "Ушел на обед.")
            works.update(f"B{lr}", name)
            works.update(f"C{lr}", surname)
            works.update(f"F{lr}", "Ушел на обед.")
            works.update(f"G{lr}", message.from_user.id)
            works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
            bot.send_message(message.from_user.id,
                             "Я вас отметил, можете идти на обед.",
                             reply_markup=mk2)
        if message.text == "Я на рабочем месте":
            c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
            c.execute("SELECT lunch_timestamp FROM debug WHERE id={}".format(message.from_user.id))
            t2 = c.fetchone()[0]
            works.update(f"A{lr}", "Вернулся с обеда")
            works.update(f"B{lr}", name)
            works.update(f"C{lr}", surname)
            works.update(f"G{lr}", message.from_user.id)
            t = time.time() - float(t2)
            works.update(f"F{lr}", "Вернулся с обеда")
            works.update(f"H{lr}", "{}".format(str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S"))))
            bot.send_message(message.from_user.id,
                             "Спасибо. Хорошего дня.",
                             reply_markup=mk)
        if message.text == "На перекур":
            works.update(f"A{lr}", "Ушел на перекур")
            works.update(f"B{lr}", name)
            works.update(f"C{lr}", surname)
            works.update(f"F{lr}", "Ушел на перекур")
            works.update(f"G{lr}", message.from_user.id)
            works.update(f"H{lr}", "{}".format(str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S"))))
            bot.send_message(message.from_user.id, "Я вас отметил. Как вернетесь нажмите на кнопку.", reply_markup=mk3)
            c.execute("UPDATE debug SET smoke_timestamp='{}' WHERE id={}".format(time.time(), message.from_user.id))
            c.execute("UPDATE users SET step='smoking' WHERE id={}".format(message.from_user.id))
        if message.text == "Я вернулся":
            bot.send_message(message.from_user.id, "Хорошо. Я зафиксировал время перекура.", reply_markup=mk)
            c.execute("SELECT smoke_timestamp FROM debug WHERE id={}".format(message.from_user.id))
            time2 = c.fetchone()[0]
            t = time.time() - float(time2)
            works.update(f"A{lr}", "Вернулся с перекура")
            works.update(f"B{lr}", name)
            works.update(f"C{lr}", surname)
            works.update(f"F{lr}", "Вернулся с перекура")
            works.update(f"G{lr}", message.from_user.id)
            works.update(f"H{lr}", str(datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")))
            c.execute("UPDATE users SET step='main_menu' WHERE id={}".format(message.from_user.id))
    db.close()

# getLocation()3
scheduler.add_job(workFix, "cron", hour='0')
scheduler.add_job(getLocation, 'cron', hour='9', day_of_week='mon-fri')
scheduler.add_job(getLocation2, 'cron', hour='18', day_of_week='mon-fri')
scheduler.start()

bot.infinity_polling()

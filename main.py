import telebot
import requests
import random
import string
import time
import os
from telebot import types
from datetime import datetime
from io import BytesIO

# --- ВСТАВЬ СВОЙ ТОКЕН ТУТ ---
API_TOKEN = '8513383405:AAF0bQ29FmCzcoSTpMbUtXuCExDDrrWrwzw'
bot = telebot.TeleBot(API_TOKEN)

class PowerFarmer:
    def __init__(self):
        self.api_url = "https://api.mail.tm"
        self.domains = []
        self.active_tasks = {} # Храним данные сессий юзеров

    def get_headers(self):
        v = random.randint(128, 133)
        return {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Origin": "https://mail.tm",
            "Referer": "https://mail.tm/"
        }

    def update_domains(self):
        try:
            res = requests.get(f"{self.api_url}/domains", timeout=10)
            self.domains = [d['domain'] for d in res.json()['hydra:member']]
        except:
            self.domains = ["mail.tm", "vintagereads.com", "frylinks.com"]

    def register(self):
        # Реалистичные префиксы
        names = ["nick", "user", "pro", "dev", "tech", "boss", "admin", "mail"]
        login = f"{random.choice(names)}.{''.join(random.choices(string.ascii_lowercase, k=4))}{random.randint(100, 999)}"
        domain = random.choice(self.domains) if self.domains else "mail.tm"
        email = f"{login}@{domain}"
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=14))

        try:
            # Минимальный КД для обхода защиты (человеческий фактор)
            time.sleep(random.uniform(0.5, 1.0))
            res = requests.post(
                f"{self.api_url}/accounts",
                json={"address": email, "password": pwd},
                headers=self.get_headers(),
                timeout=15
            )
            if res.status_code == 201:
                return f'"{email}":"{pwd}"'
            elif res.status_code == 429:
                return "LIMIT"
        except:
            return "ERROR"
        return "FAILED"

farmer = PowerFarmer()

@bot.message_handler(commands=['start', 'farm', 'help'])
def welcome(message):
    farmer.update_domains()
    text = (
        "👋 **Привет! Я бот для фарма Mail.tm**\n\n"
        "🔹 Работаю на твоем IP (хостинга)\n"
        "🔹 Без задержек по 2 минуты\n"
        "🔹 Выдаю готовый файл в конце\n\n"
        "👉 **Сколько почт нужно сделать?** (Просто введи число)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text.isdigit())
def start_farming(message):
    uid = message.from_user.id
    count = int(message.text)
    
    if count > 500:
        return bot.reply_to(message, "❌ Слишком много за раз. Давай до 500.")

    farmer.active_tasks[uid] = {"running": True, "accs": []}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛑 ОСТАНОВИТЬ И СОХРАНИТЬ", callback_data="stop"))
    
    status_msg = bot.send_message(message.chat.id, f"🎬 Начинаю фарм {count} почт...", reply_markup=markup)
    
    success = 0
    try:
        while success < count and farmer.active_tasks[uid]["running"]:
            res = farmer.register()
            
            if ":" in str(res):
                success += 1
                farmer.active_tasks[uid]["accs"].append(res)
                # Отправляем лог в чат (каждые 1-2 почты)
                bot.send_message(message.chat.id, f"✅ `{res}`", parse_mode="Markdown")
            
            elif res == "LIMIT":
                bot.send_message(message.chat.id, "⏳ Лимит IP! Жду 15 сек...")
                time.sleep(15)
            
            else:
                time.sleep(1)

        send_final_file(message.chat.id, uid)

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка в процессе: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "stop")
def stop_btn(call):
    uid = call.from_user.id
    if uid in farmer.active_tasks:
        farmer.active_tasks[uid]["running"] = False
        bot.answer_callback_query(call.id, "Останавливаю и готовлю файл...")

def send_final_file(chat_id, uid):
    if uid in farmer.active_tasks and farmer.active_tasks[uid]["accs"]:
        accs_list = farmer.active_tasks[uid]["accs"]
        count = len(accs_list)
        
        # Формируем файл в формате "почта":"пароль"
        content = "\n".join(accs_list)
        file = BytesIO(content.encode('utf-8'))
        file.name = f"farm_results_{count}.txt"
        
        bot.send_message(chat_id, f"🏁 **Готово!**\nВсего нафармлено: {count}")
        bot.send_document(chat_id, file, caption="📂 Лови свой файл с аккаунтами")
        
        # Очистка памяти
        del farmer.active_tasks[uid]
    else:
        bot.send_message(chat_id, "❌ Ни одного аккаунта не было создано.")

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Мясорубка запущена!")
    bot.polling(none_stop=True)

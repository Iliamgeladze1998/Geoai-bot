import telebot
import g4f
import json
import os
from telebot.apihelper import ApiTelegramException

# კონფიგურაცია
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=15)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

def save_data(d):
    with open(DATA_FILE, 'w') as f: json.dump(d, f)

data = load_data()

# 🛡️ პოლიტიკა
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია.\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

# 🌍 ენის "სარკისებური" ინსტრუქცია (აგვარებს ენის არევის პრობლემას)
instruction = (
    "Your name is GeoAI. Your creator is Ilia Mgeladze. "
    "MANDATORY RULE: Detect the user's language and respond ONLY in that language. "
    "If the user writes in English, reply in English. If in Georgian, reply in Georgian. "
    "Never use other languages. Keep your persona professional and pragmatic 😊."
)

# 🔍 რეალური დროის ვალიდატორი (ბლოკავს #General-ს და დუბლიკატებს)
def is_session_valid(u_id):
    if u_id not in data["topics"]: return False
    try:
        # აიძულებს ბოტს "შეეხოს" ჩატს. თუ ჩატი წაშლილია, აქ მოხდება Error 400.
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=data["topics"][u_id])
        return True
    except ApiTelegramException as e:
        if "thread not found" in e.description.lower():
            if u_id in data["topics"]: del data["topics"][u_id]
            save_data(data)
            return False
        return True # ლაგის შემთხვევაში არ ვშლით
    except: return True

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if is_session_valid(u_id):
        bot.send_message(message.chat.id, "თქვენ უკვე გაიარეთ ვერიფიკაცია! 😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია საუბრის დასაწყებად:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id, u_name = str(message.from_user.id), message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        # დუბლიკატების ბლოკი
        if is_session_valid(u_id):
            bot.send_message(u_id, "თქვენ უკვე გაქვთ აქტიური ჩატი ჯგუფში! 😊")
            return

        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["phones"][u_id] = phone
            save_data(data)
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში თემის შექმნისას.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინის პასუხის გადამისამართება
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🛑 მთავარი ბარიერი: თუ ჩატი ჯგუფში არ არის, საუბარი წყდება და ითხოვს ვერიფიკაციას
    if not is_session_valid(u_id):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"თქვენი სესია განახლდა.\n\n{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
        return

    # 🚀 AI პასუხი
    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        # ვიყენებთ სისტემურ ინსტრუქციას ენის კონტროლისთვის
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4, 
            messages=[{"role": "system", "content": instruction}, {"role": "user", "content": message.text}]
        )
        
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    except:
        bot.reply_to(message, "ხარვეზია, სცადეთ მოგვიანებით 😊")

bot.polling(none_stop=True, timeout=120)

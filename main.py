import telebot
import g4f
import json
import os
from telebot.apihelper import ApiTelegramException

# კონფიგურაცია
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=4)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

def save_data(d):
    try:
        with open(DATA_FILE, 'w') as f: json.dump(d, f)
    except Exception as e:
        print(f"Error saving data: {e}")

data = load_data()

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "მიმოწერები ხელმისაწვდომია ადმინისტრაციისთვის.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

instruction = (
    "Your name is GeoAI. Your creator is Ilia Mgeladze. "
    "STRICT RULE: Always reply in the EXACT same language the user is using. "
    "Stay consistent and professional 😊."
)

# 🔍 გაუმჯობესებული შემოწმება (ლაგის და რესტარტის დაცვით)
def check_topic_exists(u_id):
    if u_id not in data["topics"]: return False
    try:
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=data["topics"][u_id])
        return True
    except ApiTelegramException as e:
        if "message thread not found" in e.description.lower():
            return False
        return True # თუ სხვა ერორია (მაგ. ლაგი), მაინც ვენდობით არსებულ ID-ს
    except: return True

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if check_topic_exists(u_id):
        bot.send_message(message.chat.id, "თქვენ უკვე გაიარეთ ვერიფიკაცია! 😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id = str(message.from_user.id)
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        # 🛡️ დუბლიკატებისგან დაცვის მექანიზმი
        if check_topic_exists(u_id):
            bot.send_message(u_id, "თქვენ უკვე გაქვთ აქტიური ჩატი! 😊")
            return

        try:
            # ვქმნით თემას
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["phones"][u_id] = phone
            save_data(data) # მონაცემების მომენტალური შენახვა
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
        except Exception as e:
            bot.send_message(u_id, "ხარვეზია, სცადეთ მოგვიანებით.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინის პასუხი
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # ვერიფიკაციის ვალიდაცია მესიჯის გაგზავნამდე
    if not check_topic_exists(u_id):
        # თუ მონაცემები წაშლილია (რესტარტის გამო), ვთხოვთ ვერიფიკაციას
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "თქვენი სესია განახლდა. გთხოვთ, გაიაროთ ვერიფიკაცია თავიდან 👇", reply_markup=markup)
        return

    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        full_prompt = f"{instruction}\n\nUser: {message.text}"
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
        
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    except:
        bot.reply_to(message, "ხარვეზია, სცადეთ მოგვიანებით 😊")

bot.polling(none_stop=True, timeout=90)

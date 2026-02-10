import telebot
import g4f
import json
import os
from telebot.apihelper import ApiTelegramException

# კონფიგურაცია
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

# Threaded=True სწრაფი რეაგირებისთვის
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

def save_data(d):
    with open(DATA_FILE, 'w') as f: json.dump(d, f)

data = load_data()

# 🛡️ პოლიტიკა + ვერიფიკაციის ტექსტი
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "მიმოწერები ხელმისაწვდომია ადმინისტრაციისთვის მომსახურების ხარისხის კონტროლისთვის.\n\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

# 🌍 მკაცრი ინსტრუქცია ენის შესახებ (აგვარებს 1000003866.jpg-ის პრობლემას)
instruction = (
    "Your name is GeoAI. Your creator is Ilia Mgeladze. "
    "SYSTEM RULE: Always respond ONLY in the language the user is currently using. "
    "If the user speaks English, reply in English. If Georgian, reply in Georgian. "
    "NEVER mix languages like Russian or others. Be consistent and professional 😊."
)

# 🔍 მკაცრი შემოწმება (აგვარებს Topic-ის წაშლის დეტექციას)
def is_verified(u_id):
    if u_id not in data["topics"]:
        return False
    try:
        # ვცდილობთ ჩატში მოქმედების იმიტაციას. თუ ჩატი წაშლილია, ტელეგრამი ეგრევე ერორს მოგვცემს.
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=data["topics"][u_id])
        return True
    except ApiTelegramException as e:
        # თუ თემა ვერ მოიძებნა (Error 400), ვშლით მონაცემებს და ვაბრუნებთ False-ს
        if "thread not found" in e.description.lower():
            if u_id in data["topics"]: del data["topics"][u_id]
            save_data(data)
            return False
        return True # სხვა ერორებისას (ლაგისას) არ ვშლით
    except:
        return True

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if is_verified(u_id):
        bot.send_message(message.chat.id, "თქვენ უკვე გაიარეთ ვერიფიკაცია! 😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გთხოვთ, გაიაროთ ვერიფიკაცია საუბრის დასაწყებად:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id = str(message.from_user.id)
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        # თუ უკვე არსებობს და ცოცხალია, ახალს არ ვქმნით
        if is_verified(u_id):
            bot.send_message(u_id, "ვერიფიკაცია უკვე გავლილი გაქვთ! 😊")
            return

        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["phones"][u_id] = phone
            save_data(data)
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! ახლა შეგიძლიათ მომწეროთ 😊")
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში თემის შექმნისას.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინის პასუხი
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🛑 მთავარი ფილტრი: თუ ჩატი წაშლილია, ვაჩვენებთ Privacy Policy-ს და ვბლოკავთ საუბარს
    if not is_verified(u_id):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"თქვენი სესია განახლდა.\n\n{PRIVACY_TEXT}\n\n👇 გთხოვთ, გაიაროთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
        return

    # 🚀 AI პასუხი და გადაგზავნა
    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        full_prompt = f"{instruction}\n\nUser: {message.text}"
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
        
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    except:
        bot.reply_to(message, "ხარვეზია, სცადეთ მოგვიანებით 😊")

bot.polling(none_stop=True, timeout=120)

import telebot
import g4f
import json
import os
from telebot.apihelper import ApiTelegramException

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

# ოპტიმიზებული პოლინგი
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

# ინსტრუქცია ენის და იდენტობისთვის
instruction = (
    "Your name is GeoAI. Your creator is Ilia Mgeladze. "
    "MANDATORY: Always reply in the EXACT same language as the user. "
    "If the user speaks English, you MUST speak English only. "
    "Be professional and concise 😊."
)

# 🔍 ჭკვიანი შემოწმება (აგვარებს 1000003870.jpg-ის პრობლემას)
def check_verification_robust(u_id):
    if u_id not in data["topics"]:
        return False
    try:
        # მხოლოდ typing-ს ვამოწმებთ, რომ არ გადავტვირთოთ სისტემა
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=data["topics"][u_id])
        return True
    except ApiTelegramException as e:
        # აი აქაა გასაღები: ვშლით მხოლოდ თუ ტელეგრამი გვეუბნება "Thread not found" (Error 400)
        if e.error_code == 400 and "thread not found" in e.description.lower():
            if u_id in data["topics"]: del data["topics"][u_id]
            save_data(data)
            return False
        # თუ სხვა ერორია (მაგ. Timeout/Lag), ვთვლით რომ ჩატი მაინც არსებობს!
        return True
    except:
        return True

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if check_verification_robust(u_id):
        bot.send_message(message.chat.id, "თქვენ უკვე გაიარეთ ვერიფიკაცია! 😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "გთხოვთ, გაიაროთ ვერიფიკაცია საუბრის დასაწყებად 👇", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id, u_name = str(message.from_user.id), message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        # თუ ჩატი უკვე არსებობს, მეორეს აღარ ვქმნით (აგვარებს დუბლიკატებს)
        if check_verification_robust(u_id):
            bot.send_message(u_id, "თქვენ უკვე გაქვთ აქტიური ჩატი! 😊")
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

    # ადმინის პასუხი
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🛑 შემოწმება ლაგის გათვალისწინებით
    if not check_verification_robust(u_id):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "სესია განახლდა. გთხოვთ, გაიაროთ ვერიფიკაცია 👇", reply_markup=markup)
        return

    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, 
                                            messages=[{"role": "user", "content": f"{instruction}\n\nUser: {message.text}"}])
        
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    except:
        bot.reply_to(message, "ხარვეზია, სცადეთ მოგვიანებით 😊")

# გაზრდილი ტაიმაუტი სტაბილური კავშირისთვის
bot.polling(none_stop=True, timeout=123)

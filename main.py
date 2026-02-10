import telebot
import g4f
import json
import os
from telebot.apihelper import ApiTelegramException

# კონფიგურაცია
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

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

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "მიმოწერები ხელმისაწვდომია ადმინისტრაციისთვის მომსახურების ხარისხის კონტროლისთვის.\n\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

instruction = (
    "Your name is GeoAI. Your creator is Ilia Mgeladze. "
    "SYSTEM RULE: Always respond ONLY in the same language the user uses."
)

# 🔍 ეს ფუნქციაა "Gatekeeper" - ის აიძულებს ბოტს რეალურ შემოწმებას
def force_check_group_topic(u_id):
    # თუ JSON-ში საერთოდ არ არის იუზერი
    if u_id not in data["topics"]:
        return False
    
    try:
        t_id = data["topics"][u_id]
        # ⚡ ფიზიკური ტესტი: ვცდილობთ "typing" სტატუსის გაგზავნას ამ კონკრეტულ თემაში
        # თუ თემა წაშლილია, ტელეგრამი მომენტალურად დააბრუნებს Error 400-ს
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=t_id)
        return True # ჩატი ნაპოვნია და ცოცხალია
    except ApiTelegramException as e:
        # თუ ერორი გვეუბნება, რომ თემა არ არსებობს
        if "thread not found" in e.description.lower():
            # 🛑 ვშლით JSON-იდან და ვაიძულებთ ვერიფიკაციას
            if u_id in data["topics"]: del data["topics"][u_id]
            if u_id in data["phones"]: del data["phones"][u_id]
            save_data(data)
            return False
        # სხვა ტექნიკური ერორისას (მაგ. ლაგი) ვენდობით არსებულ ჩანაწერს
        return True
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if force_check_group_topic(u_id):
        bot.send_message(message.chat.id, "თქვენ უკვე გაიარეთ ვერიფიკაცია! 😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id, u_name = str(message.from_user.id), message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        # თუ ჩატი უკვე არსებობს და ცოცხალია, ახალს არ ვქმნით
        if force_check_group_topic(u_id):
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

    # ადმინის პასუხის ლოგიკა (უცვლელია)
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🛑 მთავარი ბარიერი: თუ ჩატი ჯგუფში არ არის, საუბარი აქ წყდება!
    if not force_check_group_topic(u_id):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"თქვენი სესია განახლდა.\n\n{PRIVACY_TEXT}\n\n👇 გთხოვთ, გაიაროთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
        return # 👈 ეს არის ყველაზე მნიშვნელოვანი Return, რომელიც ბლოკავს მესიჯს

    # 🚀 თუ ყველაფერი რიგზეა - AI პასუხი
    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, 
                                            messages=[{"role": "user", "content": f"{instruction}\n\nUser: {message.text}"}])
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    except:
        bot.reply_to(message, "ხარვეზია, სცადეთ მოგვიანებით 😊")

bot.polling(none_stop=True, timeout=120)

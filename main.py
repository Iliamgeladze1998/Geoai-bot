import telebot
import g4f
import json
import os
from telebot.apihelper import ApiTelegramException

# კონფიგურაცია
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=25)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

def save_data(d):
    with open(DATA_FILE, 'w') as f: json.dump(d, f)

data = load_data()

# იდენტობა და ენა
instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე (ელ-ფოსტა: mgeladzeilia39@gmail.com). "
    "MANDATORY: Detect the user's language and respond ONLY in that language. "
    "If the user speaks English, you MUST speak English only. "
    "იყავი სხარტი, ძალიან სწრაფი და პროფესიონალი 😊."
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია.\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

# 🔍 Gatekeeper: ამოწმებს არსებობს თუ არა თემა ჯგუფში
def is_session_valid(u_id):
    if u_id not in data["topics"]: return False
    try:
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=data["topics"][u_id])
        return True
    except ApiTelegramException as e:
        if "thread not found" in e.description.lower():
            if u_id in data["topics"]: del data["topics"][u_id]
            save_data(data)
            return False
        return True
    except: return True

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if is_session_valid(u_id):
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
        
        if is_session_valid(u_id):
            bot.send_message(u_id, "ვერიფიკაცია უკვე გავლილი გაქვთ! 😊")
            return

        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["phones"][u_id] = phone
            save_data(data)
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინის პასუხი
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # ვალიდაცია მესიჯის გაპარვის საწინააღმდეგოდ
    if not is_session_valid(u_id):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"სესია განახლდა.\n\n{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
        return

    # 🚀 AI პასუხის გენერაცია
    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        # ვცდილობთ რამდენიმე მოდელს, რომ პასუხი გარანტირებული იყოს
        response = ""
        for model in [g4f.models.gpt_4o, g4f.models.gpt_4, g4f.models.default]:
            try:
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "system", "content": instruction}, {"role": "user", "content": message.text}]
                )
                if response: break
            except: continue

        if response:
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
        else:
            raise Exception("All models failed")
            
    except:
        bot.reply_to(message, "სისტემას ვაახლებ, გთხოვთ მომწეროთ 1 წუთში 😊")

bot.polling(none_stop=True, timeout=120)

import telebot
import g4f
import json
import os
import time
from telebot.apihelper import ApiTelegramException

# კონფიგურაცია
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

# ვზრდით ვორკერების რაოდენობას
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=30)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read()
                return json.loads(content) if content else {"topics": {}, "phones": {}}
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

def save_data(d):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(d, f, indent=4)
    except Exception as e:
        print(f"Save error: {e}")

data = load_data()

# 🌍 იდენტობა და ენის მკაცრი ინსტრუქცია
instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე (ელ-ფოსტა: mgeladzeilia39@gmail.com). "
    "MANDATORY RULE: Always respond ONLY in the same language the user is currently using. "
    "If the user speaks English, you MUST speak English only. If Georgian - Georgian. "
    "იყავი სხარტი, პროფესიონალი და ყოველთვის გახსოვდეს შენი შემქმნელი 😊."
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია.\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

# 🔍 სტაბილური ვალიდაცია (აღარ წაშლის მონაცემებს უმიზეზოდ)
def is_session_ok(u_id):
    u_id = str(u_id)
    if u_id not in data["topics"]:
        return False
    try:
        # მხოლოდ იმ შემთხვევაში ვაუქმებთ, თუ ტელეგრამი დაადასტურებს ჩატის წაშლას
        bot.send_chat_action(ADMIN_GROUP_ID, 'typing', message_thread_id=data["topics"][u_id])
        return True
    except ApiTelegramException as e:
        if "thread not found" in e.description.lower():
            if u_id in data["topics"]: del data["topics"][u_id]
            save_data(data)
            return False
        return True # ლაგის ან სხვა ერორის დროს ვენდობით არსებულ სესიას
    except:
        return True

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if is_session_ok(u_id):
        bot.send_message(message.chat.id, "ვერიფიკაცია უკვე გავლილი გაქვთ! 😊")
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
        
        if is_session_ok(u_id):
            bot.send_message(u_id, "თქვენ უკვე გაქვთ აქტიური ჩატი! 😊")
            return

        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["phones"][u_id] = phone
            save_data(data)
            time.sleep(1) # პატარა პაუზა სინქრონიზაციისთვის
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! ახლა შეგიძლიათ მომწეროთ 😊")
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში თემის შექმნისას.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🛑 ვერიფიკაციის შემოწმება
    if not is_session_ok(u_id):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"სესია განახლდა.\n\n{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
        return

    # 🚀 AI პასუხის მრავალდონიანი გენერაცია
    try:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        response = None
        # ვცდილობთ სხვადასხვა მოდელებს წარმატებამდე
        for model in [g4f.models.gpt_4o, g4f.models.gpt_4, g4f.models.gpt_35_turbo]:
            try:
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "system", "content": instruction}, {"role": "user", "content": message.text}],
                    timeout=30
                )
                if response and len(response) > 2: break
            except: continue

        if response:
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
        else:
            bot.reply_to(message, "ამჟამად AI პროვაიდერები დაკავებულია, გთხოვთ სცადოთ 1 წუთში 😊")
    except:
        bot.reply_to(message, "სერვერის მცირე შეფერხებაა, გთხოვთ მომწეროთ თავიდან 😊")

bot.polling(none_stop=True, timeout=123)

import telebot
import g4f
import json
import os

# ძირითადი მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True)

# მეხსიერების ჩატვირთვა
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

data = load_data()

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# AI-ს იდენტობა
instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე (mgeladzeilia39@gmail.com). "
    "ყოველთვის უპასუხე იმავე ენაზე, რაზეც მომხმარებელი გწერს. "
    "იყავი სწრაფი, ზუსტი და მეგობრული 😊."
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრისთვის აუცილებელია ვერიფიკაცია.\n"
    "🛡️ თქვენი ნომერი ჩანს მხოლოდ ადმინისტრაციისთვის.\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    # თუ მეხსიერებაშია, აღარაფერს ვთხოვთ
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "თქვენ უკვე ვერიფიცირებული ხართ! რით შემიძლია დაგეხმაროთ? 😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    u_id = str(message.from_user.id)
    if message.contact and u_id not in data["topics"]:
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        try:
            # ვქმნით ტოპიკს ერთხელ და სამუდამოდ
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            save_data()
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! შეგიძლიათ მწეროთ 😊")
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინის პასუხის გადაგზავნა იუზერთან
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # იუზერის მესიჯის დამუშავება
    if u_id in data["topics"]:
        t_id = data["topics"][u_id]
        # ვაგზავნით ადმინთან
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        # AI პასუხი (GPT-4o სისწრაფისთვის)
        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4o,
                messages=[{"role": "system", "content": instruction}, {"role": "user", "content": message.text}]
            )
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
        except:
            bot.reply_to(message, "სისტემა დაკავებულია, სცადეთ თავიდან 😊")
    else:
        start(message)

bot.polling(none_stop=True)

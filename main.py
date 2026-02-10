import telebot
import g4f
import json
import os

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN)

# მონაცემების ჩატვირთვა/შენახვის ფუნქციები
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return {"topics": {}, "phones": {}, "counts": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f)

data = load_data()

instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "მიეცი ეს მეილი: mgeladzeilia39@gmail.com. "
    "ისაუბრე ბუნებრივი ქართულით, იყავი პრაგმატული და სხარტი 😊."
)

def send_stars_invoice(chat_id):
    try:
        bot.send_invoice(
            chat_id, title="GeoAI-ს მხარდაჭერა ✨",
            description="დაუჭირე მხარი პროექტს 🚀",
            provider_token="", currency="XTR",
            prices=[telebot.types.LabeledPrice(label="მხარდაჭერა", amount=50)],
            invoice_payload="geoai_support"
        )
    except: pass

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
    bot.send_message(message.chat.id, "GeoAI - საუბრისთვის გაიარე ვერიფიკაცია 👇", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id = str(message.from_user.id)
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        data["phones"][u_id] = phone
        data["counts"][u_id] = 0
        
        # ქმნის Topic-ს მხოლოდ თუ არ არსებობს
        if u_id not in data["topics"]:
            try:
                topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
                data["topics"][u_id] = topic.message_thread_id
            except: pass
        
        save_data(data)
        bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
        send_stars_invoice(u_id)

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინის პასუხი
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, thread_id in data["topics"].items():
            if thread_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🛑 ვერიფიკაციის შემოწმება და მუდმივი შეხსენება
    if u_id not in data["phones"]:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "საუბრის დასაწყებად აუცილებელია ვერიფიკაცია 😊 👇", reply_markup=markup)
        return

    # 40 მესიჯის კონტროლი
    data["counts"][u_id] = data["counts"].get(u_id, 0) + 1
    if data["counts"][u_id] % 40 == 0:
        send_stars_invoice(u_id)
    save_data(data)

    # მესიჯის გადაგზავნა არსებულ Topic-ში
    thread_id = data["topics"].get(u_id)
    if thread_id:
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=thread_id)
        try:
            full_prompt = f"{instruction}\n\nმომხმარებელი: {message.text}"
            response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=thread_id)
        except:
            bot.reply_to(message, "სისტემას ვანახლებ 😊")

print("SERVER: OPERATIONAL WITH PERSISTENCE")
bot.polling(none_stop=True)

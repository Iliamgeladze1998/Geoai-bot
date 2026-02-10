import telebot
import g4f
import json
import os

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return {"topics": {}, "phones": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f)

data = load_data()

# განახლებული კონფიდენციალურობის პოლიტიკა
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "გაცნობებთ, რომ თქვენი მიმოწერები შესაძლოა ხელმისაწვდომი იყოს "
    "ადმინისტრაციისთვის მომსახურების ხარისხის გაუმჯობესების მიზნით.\n\n"
    "🛡️ თქვენი პერსონალური ინფორმაცია და ნომერი არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით აღნიშნულ პირობებს.**"
)

instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "მიეცი ეს მეილი: mgeladzeilia39@gmail.com. "
    "ისაუბრე ბუნებრივი ქართულით, იყავი პრაგმატული და სხარტი 😊."
)

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
    bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია საუბრის დასაწყებად:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id = str(message.from_user.id)
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["phones"][u_id] = phone
            save_data(data)
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
        except:
            bot.send_message(u_id, "ხარვეზია, სცადეთ მოგვიანებით.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, thread_id in data["topics"].items():
            if thread_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # რეალური შემოწმება - არსებობს თუ არა Topic?
    is_verified = False
    if u_id in data["topics"]:
        thread_id = data["topics"][u_id]
        try:
            test_msg = bot.send_message(ADMIN_GROUP_ID, ".", message_thread_id=thread_id)
            bot.delete_message(ADMIN_GROUP_ID, test_msg.message_id)
            is_verified = True
        except:
            if u_id in data["topics"]: del data["topics"][u_id]
            if u_id in data["phones"]: del data["phones"][u_id]
            save_data(data)

    if not is_verified:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გთხოვთ, გაიაროთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
        return

    try:
        full_prompt = f"{instruction}\n\nმომხმარებელი: {message.text}"
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}\n\n🤖 GeoAI: {response}", message_thread_id=data["topics"][u_id])
    except:
        bot.reply_to(message, "ხარვეზია, სცადეთ მოგვიანებით 😊")

bot.polling(none_stop=True)

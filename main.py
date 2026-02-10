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
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "მიეცი ეს მეილი: mgeladzeilia39@gmail.com. "
    "ისაუბრე ბუნებრივი ქართულით, იყავი პრაგმატული და სხარტი 😊."
)

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    # თუ იუზერი ბაზაშია, პირდაპირ მივესალმოთ
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "თქვენ უკვე გაიარეთ ვერიფიკაცია. შეგიძლიათ მწეროთ! 😊")
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
        
        # თუ ჩატი უკვე გვიწერია ბაზაში
        if u_id in data["topics"]:
            bot.send_message(u_id, "ვერიფიკაცია უკვე გავლილი გაქვთ! 😊")
            return

        try:
            # ვქმნით Topic-ს სახელით და ნომრით
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
        for user_id, thread_id in data["topics"].items():
            if thread_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 🔍 შემოწმება: გვაქვს თუ არა ეს იუზერი ბაზაში?
    if u_id not in data["topics"]:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გთხოვთ, გაიაროთ ვერიფიკაცია საუბრის დასაწყებად:", reply_markup=markup, parse_mode="Markdown")
        return

    # 🚀 მესიჯის გაგზავნა ჯგუფში (და რეალური შემოწმება)
    try:
        thread_id = data["topics"][u_id]
        # ვცდილობთ მესიჯის გადაგზავნას ჯგუფის თემაში
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=thread_id)
        
        # თუ მესიჯი გაიგზავნა, ე.ი. Topic ცოცხალია -> AI პასუხი
        full_prompt = f"{instruction}\n\nმომხმარებელი: {message.text}"
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=thread_id)
        
    except Exception as e:
        # თუ ერორია, ესე იგი Topic წაშლილია! (ან ბოტი აღარაა ადმინი)
        if u_id in data["topics"]: del data["topics"][u_id]
        save_data(data)
        
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "თქვენი საუბრის თემა ჯგუფში ვერ მოიძებნა. გთხოვთ, გაიაროთ ვერიფიკაცია თავიდან 😊", reply_markup=markup)

bot.polling(none_stop=True)

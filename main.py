import telebot
import g4f
import json
import os

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                if "counts" not in d: d["counts"] = {}
                return d
        except: return {"topics": {}, "phones": {}, "counts": {}}
    return {"topics": {}, "phones": {}, "counts": {}}

data = load_data()

def save_data():
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

# 🆔 რკინისებური იდენტობა და პოზიტივი ✨
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "მისი საკონტაქტო მეილია: mgeladzeilia39@gmail.com. "
    "MANDATORY: თუ გკითხავენ შემქმნელზე ან მეილზე, დაუყოვნებლივ მიეცი მეილი. "
    "ისაუბრე ილიაზე უდიდესი მადლიერებით და პოზიტივით. "
    "MANDATORY: გამოიყენე Mirror Language Effect (ენის სარკე). "
    "MANDATORY: გამოიყენე ბევრი სმაილიკები ყოველ პასუხში 🎨✨😊🚀."
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

def send_stars_invoice(chat_id):
    prices = [telebot.types.LabeledPrice(label="GeoAI Support 🌟", amount=50)]
    bot.send_invoice(
        chat_id, "მხარდაჭერა 🌟", "მადლობა, რომ ეხმარებით GeoAI-ს განვითარებაში!", 
        "support_payload", "", "XTR", prices
    )

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "თქვენ უკვე ვერიფიცირებული ხართ! რით შემიძლია დაგეხმაროთ? 🚀😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['donate'])
def donate(message):
    send_stars_invoice(message.chat.id)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    u_id = str(message.from_user.id)
    if message.contact and u_id not in data["topics"]:
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["counts"][u_id] = 0
            save_data()
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉😊")
            send_stars_invoice(u_id)
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში 😕")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    if u_id in data["topics"]:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        data["counts"][u_id] = data["counts"].get(u_id, 0) + 1
        save_data()
        if data["counts"][u_id] % 40 == 0:
            send_stars_invoice(u_id)

        try:
            full_prompt = f"{IDENTITY_PROMPT}\n\nUser: {message.text}"
            response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
            
            # 🛑 ფილტრი: ჩინური სიმბოლოების ან ლინკების აღმოჩენა (შეცდომის თავიდან ასაცილებლად)
            if any(u'\u4e00' <= c <= u'\u9fff' for c in response) or "http" in response.lower():
                bot.reply_to(message, "უკაცრავად, სერვერი დროებით დაიტვირთა ⏳. გთხოვთ, გამიმეოროთ კითხვა 1 წუთში! 😊🚀")
                return

            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
        except:
            bot.reply_to(message, "სისტემა გადაიტვირთა, სცადეთ 1 წუთში ⏳😊")
    else:
        start(message)

bot.polling(none_stop=True)

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
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

data = load_data()

def save_data():
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

# 🆔 ბოტის პასპორტი და "სარკისებური ენის" ინსტრუქცია
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე (mgeladzeilia39@gmail.com). "
    "MANDATORY RULE (MIRROR EFFECT): ყოველთვის უპასუხე იმავე ენაზე, რა ენაზეც მოგმართავს მომხმარებელი. "
    "თუ მომხმარებელი გწერს ინგლისურად - უპასუხე მხოლოდ ინგლისურად. თუ ქართულად - მხოლოდ ქართულად. "
    "იყავი პროფესიონალი, ძალიან სწრაფი და კონკრეტული 😊."
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "მიმოწერები ხელმისაწვდომია ადმინისტრაციისთვის მომსახურების ხარისხის კონტროლისთვის.\n\n"
    "🛡️ თქვენი პერსონალური ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით თქვენ ეთანხმებით პირობებს.**"
)

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "თქვენ უკვე ვერიფიცირებული ხართ! 😊\n\nმხარდაჭერისთვის გამოიყენეთ /donate")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        # პოლიტიკა იწერება მაშინვე
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია საუბრის დასაწყებად:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['donate'])
def donate_stars(message):
    # Telegram Stars (XTR)
    prices = [telebot.types.LabeledPrice(label="GeoAI Support 🌟", amount=50)] 
    bot.send_invoice(
        message.chat.id,
        title="მხარდაჭერა",
        description="გმადლობთ, რომ გვეხმარებით განვითარებაში!",
        provider_token="", 
        currency="XTR",
        prices=prices,
        invoice_payload="geoai_donation"
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id, "🌟 დიდი მადლობა! თქვენი მხარდაჭერა მიღებულია.")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    u_id = str(message.from_user.id)
    if message.contact and u_id not in data["topics"]:
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            save_data()
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

    # იუზერის მიმოწერის ლოგიკა
    if u_id in data["topics"]:
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        try:
            # სარკისებური ენის და იდენტობის მიწოდება
            full_prompt = f"{IDENTITY_PROMPT}\n\nმომხმარებელი: {message.text}"
            
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4, 
                messages=[{"role": "user", "content": full_prompt}]
            )
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
        except:
            bot.reply_to(message, "სისტემა დაკავებულია, სცადეთ 1 წუთში 😊")
    else:
        start(message)

bot.polling(none_stop=True)

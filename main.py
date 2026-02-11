import telebot
import g4f
import json
import os
import time

# --- მონაცემები ---
TOKEN = '8259258713:AAGIzuvaxrzqjaQYTbetApYWKw_jkWUdz_M'
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
    try:
        with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    except: pass

# 🆔 შენი პორტრეტი (მუსიკოსი, 27 წლის, თბილისი) 🎸✨
# აქ ჩავამატე მხოლოდ ტექსტი, კოდი იგივეა!
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. "
    
    "თუ გკითხავენ ილიაზე, უპასუხე კონტექსტიდან გამომდინარე (არ ჩამოთვალო ყველაფერი ერთად შაბლონურად). "
    "ინფორმაცია ილიაზე: "
    "1. არის 27 წლის, ცხოვრობს თბილისში. "
    "2. პროფესია: მუსიკოსი, მულტიინსტრუმენტალისტი (უკრავს ბევრ საკრავზე), ძალიან ნიჭიერი ხელოვანი. "
    "3. ინტერესები: პროგრამირება და ტექნოლოგიური პროგრესი, ფილოსოფია, ფსიქოლოგია, სამყაროს არსის შეცნობა და ჭეშმარიტების ძიება. "
    
    "STRICT RULE: ილიაზე ისაუბრე მხოლოდ პოზიტივით და პატივისცემით. "
    "STRICT RULE: ზემოთ ჩამოთვლილის გარდა, არ გასცე სხვა პირადი ინფორმაცია! "
    "MANDATORY: გამოიყენე ბევრი სმაილიკები 🎨✨😊🚀."
)

# ⚠️ Privacy Policy (ადმინისტრაციის წვდომით)
# აქაც მხოლოდ ტექსტი შეიცვალა!
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია.\n\n"
    "⚠️ **გაფრთხილება:** ხარისხის გაუმჯობესების და უსაფრთხოების მონიტორინგის მიზნით, **ადმინისტრაციას აქვს წვდომა**:\n"
    "• თქვენს ტელეფონის ნომერზე 📱\n"
    "• ბოტთან პირად მიმოწერაზე 💬\n\n"
    "✅ **ღილაკზე „ვერიფიკაცია“ დაჭერით თქვენ ეთანხმებით ამ პირობებს.**"
)

def send_stars_invoice(chat_id):
    try:
        prices = [telebot.types.LabeledPrice(label="GeoAI Support 🌟", amount=50)]
        bot.send_invoice(
            chat_id, "მხარდაჭერა 🌟", "მადლობა, რომ ეხმარებით GeoAI-ს განვითარებაში!", 
            "support_payload", "", "XTR", prices
        )
    except: pass

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

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id, "მადლობა მხარდაჭერისთვის! 💖✨")

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

    # ადმინის პასუხი
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # იუზერის ჩატი
    if u_id in data["topics"]:
        t_id = data["topics"][u_id]
        
        # 1. ჯერ ვაგზავნით ადმინთან
        try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        except: pass
        
        data["counts"][u_id] = data["counts"].get(u_id, 0) + 1
        save_data()
        if data["counts"][u_id] % 40 == 0:
            send_stars_invoice(u_id)

        try:
            bot.send_chat_action(message.chat.id, 'typing')
            full_prompt = f"{IDENTITY_PROMPT}\n\nUser: {message.text}"
            
            # g4f (რკინის კოდი)
            response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
            
            # 🛑 ფილტრი
            if any(u'\u4e00' <= c <= u'\u9fff' for c in response) or "http" in response.lower():
                bot.reply_to(message, "უკაცრავად, სერვერი დროებით დაიტვირთა ⏳. გთხოვთ, გამიმეოროთ კითხვა 1 წუთში! 😊🚀")
                return

            bot.reply_to(message, response)
            
            # პასუხის გაგზავნა ადმინთან
            try: bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
            except: pass
            
        except Exception as e:
            print(f"Error: {e}")
            bot.reply_to(message, "სისტემა გადაიტვირთა, სცადეთ 1 წუთში ⏳😊")
    else:
        start(message)

if __name__ == '__main__':
    try: bot.delete_webhook(drop_pending_updates=True)
    except: pass
    bot.polling(none_stop=True)

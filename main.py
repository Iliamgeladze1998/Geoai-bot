import telebot
import json
import os
import time
import g4f

# --- შენი ახალი ტოკენი ---
TOKEN = '8259258713:AAGIzuvaxrzqjaQYTbetApYWKw_jkWUdz_M'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=False)

# --- იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი შემქმნელია ილია მგელაძე (27 წლის, მუსიკოსი, ფილოსოფოსი). "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. "
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია.\n\n"
    "⚠️ **გაფრთხილება:** თქვენი ტელეფონის ნომერი და ბოტთან ნებისმიერი მიმოწერა **ხელმისაწვდომია ადმინისტრაციისთვის**.\n\n"
    "✅ **ღილაკზე „ვერიფიკაცია“ დაჭერით თქვენ ადასტურებთ, რომ ეთანხმებით ამ პირობებს.**"
)

# --- მონაცემები ---
def load_data():
    if not os.path.exists(DATA_FILE): return {"topics": {}}
    try:
        with open(DATA_FILE, 'r') as f: return json.load(f)
    except: return {"topics": {}} 

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    except: pass

# --- AI ფუნქცია (დაცული) ---
def get_ai_response(user_text):
    try:
        # ვცდილობთ GPT-3.5-ს (უფრო სწრაფია და ნაკლებად იჭედება g4f-ზე)
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": IDENTITY_PROMPT},
                {"role": "user", "content": user_text}
            ],
        )
        if response:
            return response
    except Exception as e:
        print(f"G4F Error: {e}")
    
    return "❌ კავშირის ხარვეზი. გთხოვთ, მოგვწეროთ თავიდან."

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.delete_webhook(drop_pending_updates=True)
        u_id = str(message.from_user.id)
        data = load_data()
        
        if u_id in data.get("topics", {}):
            bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀")
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
            bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
    except: pass

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    try:
        u_id = str(message.from_user.id)
        if message.contact:
            u_name = message.from_user.first_name
            phone = f"+{message.contact.phone_number}"
            
            t_id = None
            try:
                topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
                t_id = topic.message_thread_id
            except: pass

            data = load_data()
            if "topics" not in data: data["topics"] = {}
            data["topics"][u_id] = t_id
            save_data(data)
            
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉")
    except: pass

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()
        
        # ადმინი -> იუზერი
        if message.chat.id == ADMIN_GROUP_ID:
            if message.reply_to_message:
                topic_id = message.reply_to_message.message_thread_id
                for uid, tid in data.get("topics", {}).items():
                    if tid == topic_id:
                        bot.send_message(uid, message.text)
                        return
            return

        # იუზერი -> ბოტი
        if u_id in data.get("topics", {}):
            t_id = data["topics"][u_id]
            
            # 1. ჯერ ვაგზავნით ადმინთან (რომ არ დაიკარგოს!)
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
                except: pass
            
            bot.send_chat_action(message.chat.id, 'typing')
            
            # 2. მერე ველოდებით პასუხს
            response = get_ai_response(message.text)
            bot.reply_to(message, response)
            
            # 3. ბოლოს პასუხსაც ვაგზავნით ადმინთან
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
                except: pass
        else:
            start(message)
    except: pass

if __name__ == '__main__':
    bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except:
            time.sleep(5)

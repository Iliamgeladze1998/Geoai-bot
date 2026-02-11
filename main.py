import telebot
import json
import os
import requests
import time

# --- კონფიგურაცია ---
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
OPENROUTER_API_KEY = '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' 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

# Threaded=False აუცილებელია Koyeb-ის Free Tier-ისთვის, რომ არ გაჭედოს
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- RAM მეხსიერება (ფაილის დაზღვევა) ---
MEMORY_TOPICS = {} 

# --- იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი შემქმნელია ილია მგელაძე. "
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. \n\n"
    "⚠️ **ყურადღება:** თქვენი მონაცემები და ჩატში გაზიარებული ინფორმაცია ხელმისაწვდომია ადმინისტრაციისთვის. "
    "ეს აუცილებელია უსაფრთხოებისთვის. \n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

# --- მონაცემების მართვა ---
def load_data():
    global MEMORY_TOPICS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if "topics" in data:
                    MEMORY_TOPICS.update(data["topics"])
        except: pass
    return MEMORY_TOPICS

def save_data(user_id, topic_id):
    global MEMORY_TOPICS
    MEMORY_TOPICS[str(user_id)] = topic_id
    try:
        data = {"topics": MEMORY_TOPICS}
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except: pass

# --- AI ფუნქცია (განახლებული სახელები!) ---
def get_ai_response(user_text, chat_id):
    # ეს არის 2024 წლის თებერვლის მუშა სახელები
    models = [
        "google/gemini-2.0-flash-exp:free",      # Flash Lite-ის სწორი შემცვლელი
        "google/gemini-2.0-pro-exp-02-05:free",  # უძლიერესი უფასო მოდელი
        "huggingfaceh4/zephyr-7b-beta:free",     # Llama-ს ალტერნატივა
        "microsoft/phi-3-medium-128k-instruct:free"
    ]
    
    for model_id in models:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://koyeb.com",
                    "X-Title": "GeoAI"
                },
                data=json.dumps({
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": IDENTITY_PROMPT},
                        {"role": "user", "content": user_text}
                    ]
                }),
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
            else:
                print(f"Failed {model_id}: {response.status_code}")
                
        except Exception as e:
            print(f"Error {model_id}: {e}")
            continue

    return "❌ ბოდიში, სერვერები გადატვირთულია. სცადეთ 30 წამში! 😊"

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    topics = load_data()
    
    if u_id in topics:
        bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀\nგისმენთ.")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

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

            save_data(u_id, t_id)
            
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉")
            bot.send_message(u_id, "ახლა შეგიძლიათ მომწეროთ ნებისმიერი კითხვა! 🚀")
    except: pass

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)
    topics = load_data()

    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in topics.items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    if u_id in topics:
        t_id = topics[u_id]
        if t_id:
            try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
            except: pass
        
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text, message.chat.id)
        
        bot.reply_to(message, response)
        
        if t_id:
            try: bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
            except: pass
    else:
        start(message)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(5)

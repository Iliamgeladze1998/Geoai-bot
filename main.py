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

bot = telebot.TeleBot(TOKEN, threaded=False)

# --- იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი შემქმნელია ილია მგელაძე. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. "
)

# --- Privacy Policy (დაბრუნდა!) ---
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. \n\n"
    "⚠️ **ყურადღება:** თქვენი მონაცემები და ჩატში გაზიარებული ინფორმაცია ხელმისაწვდომია ადმინისტრაციისთვის. "
    "ეს აუცილებელია მომსახურების ხარისხის და უსაფრთხოებისთვის. \n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

# --- მონაცემების მართვა ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"topics": {}}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except: return {"topics": {}} 

def save_data(data, chat_id=None):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except: pass

# --- AI ფუნქცია (ახალი, მუშა მოდელებით) ---
def get_ai_response(user_text, chat_id):
    # განახლებული სია: ეს მოდელები ყველაზე სტაბილურია უფასოდ
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free", # ვცადოთ ისევ
        "mistralai/mistral-7b-instruct:free",              # ეს "უკვდავია"
        "qwen/qwen-2.5-vl-72b-instruct:free",               # ახალი და ძლიერი
        "microsoft/phi-3-mini-128k-instruct:free"          # სარეზერვო
    ]
    
    last_error = ""
    
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
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
            else:
                last_error = f"{model_id} -> {response.status_code}"
                print(f"Failed {model_id}: {response.status_code}")
                time.sleep(1) # ცოტა დაცდა, რომ არ დაგვბლოკონ
                
        except Exception as e:
            last_error = str(e)
            continue

    # თუ აქამდე მოვიდა, ესე იგი ყველა მოდელმა უარი თქვა
    bot.send_message(chat_id, f"⚠️ ყველა სერვერი დაკავებულია. ბოლო შეცდომა: {last_error}")
    return "❌ გთხოვთ, სცადოთ 30 წამში."

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()
        
        if u_id in data["topics"]:
            bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀\nშეგიძლიათ მომწეროთ.")
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
            # აქ დაბრუნდა Privacy Text!
            bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    try:
        u_id = str(message.from_user.id)
        if message.contact:
            u_name = message.from_user.first_name
            phone = f"+{message.contact.phone_number}"
            
            try:
                topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
                t_id = topic.message_thread_id
            except: t_id = None

            data = load_data()
            data["topics"][u_id] = t_id
            save_data(data, message.chat.id)
            
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉")
    except: pass

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()

        # ადმინის პასუხი
        if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
            for user_id, t_id in data.get("topics", {}).items():
                if t_id == message.message_thread_id:
                    bot.send_message(user_id, message.text)
                    return

        # იუზერის ჩატი
        if u_id in data.get("topics", {}):
            t_id = data["topics"][u_id]
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
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except:
            time.sleep(5)

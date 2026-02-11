import telebot
import json
import os
import requests
import time
import urllib3

# SSL გაფრთხილებების გათიშვა (დიაგნოსტიკისთვის)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- კონფიგურაცია ---
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
OPENROUTER_API_KEY = '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' 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=False)

# --- იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი შემქმნელია ილია მგელაძე."
)

# --- მონაცემების მართვა ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except: return {"topics": {}}
    return {"topics": {}}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except: pass

# --- AI ფუნქცია (DEBUG MODE 🐞) ---
def get_ai_response(user_text, chat_id):
    # ყველაზე სანდო მოდელები
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free"
    ]
    
    error_log = "" # აქ შევაგროვებთ ერორებს
    
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
                timeout=10,
                verify=False # SSL შემოწმებას ვთიშავთ!
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
            else:
                # ინახავს ერორის კოდს და ტექსტს
                error_msg = f"\n⚠️ {model_id}: Status {response.status_code} - {response.text[:100]}"
                error_log += error_msg
                print(error_msg)
                
        except Exception as e:
            error_log += f"\n❌ {model_id}: {str(e)}"
            continue

    # თუ აქამდე მოვიდა, აბრუნებს სრულ რეპორტს ჩატში
    return f"🆘 დიაგნოსტიკა:\n{error_log}\n\nგთხოვთ ეს სკრინშოტი აჩვენოთ დეველოპერს."

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    data = load_data()
    
    if u_id in data.get("topics", {}):
        bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "გთხოვთ გაიაროთ ვერიფიკაცია:", reply_markup=markup)

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
        
        bot.send_chat_action(message.chat.id, 'typing')
        # აქ ვიძახებთ დიაგნოსტიკურ ფუნქციას
        response = get_ai_response(message.text, message.chat.id)
        
        bot.reply_to(message, response)
        
        if t_id:
            try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}\n🤖 {response}", message_thread_id=t_id)
            except: pass
    else:
        start(message)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except:
            time.sleep(5)

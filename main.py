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

bot = telebot.TeleBot(TOKEN, threaded=True)

# --- იდენტობა ✨ ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი ერთადერთი შემქმნელია ილია მგელაძე (27 წლის, მუსიკოსი, ფილოსოფოსი). "
    "მასზე ისაუბრე მხოლოდ მაშინ, როცა გკითხავენ. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. გამოიყენე სმაილიკები 🎨🚀."
)

# --- მონაცემების მართვა ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except: return {"topics": {}}
    return {"topics": {}}

# --- AI ფუნქცია (მხოლოდ API, g4f-ის გარეშე) ---
def get_ai_response(user_text):
    # სიაშია 3 ყველაზე სანდო უფასო მოდელი
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free", # უსწრაფესი
        "meta-llama/llama-3.1-8b-instruct:free",           # სტაბილური
        "mistralai/mistral-7b-instruct:free"               # სათადარიგო
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
                timeout=10 # 10 წამი ვაცადოთ, რომ არ გაითიშოს
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    return data['choices'][0]['message']['content']
            
            # თუ მოდელი დაკავებულია, ვაგრძელებთ შემდეგზე
            time.sleep(1)
            
        except Exception as e:
            print(f"Error with {model_id}: {e}")
            continue

    return "❌ სერვერები გადატვირთულია. სცადეთ 10 წამში! 😊🚀"

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    u_id = str(message.from_user.id)
    if message.contact:
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data = load_data()
            data["topics"][u_id] = topic.message_thread_id
            with open(DATA_FILE, 'w') as f: json.dump(data, f)
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
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        bot.send_chat_action(message.chat.id, 'typing') # რომ გამოჩნდეს რომ წერს
        
        response = get_ai_response(message.text)
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except:
            time.sleep(5)

import telebot
import json
import os
import requests
import time

# --- მონაცემები ---
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
OPENROUTER_API_KEY = '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' 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True)

# --- AI ფუნქცია (განახლებული მოდელების ID-ებით) ---
def get_ai_response(user_text):
    # ეს სახელები ზუსტად ემთხვევა OpenRouter-ის მიმდინარე უფასო სიას
    models_to_try = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "deepseek/deepseek-chat:free"
    ]
    
    for model_id in models_to_try:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://koyeb.com",
                    "X-Title": "GeoAI Official"
                },
                data=json.dumps({
                    "model": model_id,
                    "messages": [{"role": "user", "content": user_text}]
                }),
                timeout=15
            )
            
            res_json = response.json()
            if response.status_code == 200 and 'choices' in res_json:
                return res_json['choices'][0]['message']['content']
            
            # თუ მოდელი დაკავებულია, ველოდებით 1 წამს და გადავდივართ შემდეგზე
            time.sleep(1)
            continue
                
        except:
            continue
            
    return "❌ ამ წუთას ყველა უფასო ხაზი გადატვირთულია. სცადეთ 30 წამში! 😊🚀"

# --- მონაცემების მართვა ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                if "topics" not in d: d["topics"] = {}
                return d
        except: return {"topics": {}}
    return {"topics": {}}

data = load_data()

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "თქვენ ვერიფიცირებული ხართ! 🚀😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "გაიარეთ ვერიფიკაცია საუბრის დასაწყებად: 😊🚀", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    u_id = str(message.from_user.id)
    if message.contact:
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{message.from_user.first_name}")
            data["topics"][u_id] = topic.message_thread_id
            save_data()
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉😊")
        except: bot.send_message(u_id, "ხარვეზია ჯგუფში 😕")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)
    if u_id in data.get("topics", {}):
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = get_ai_response(message.text)
        
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    else:
        start(message)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=90)
        except Exception:
            time.sleep(5)

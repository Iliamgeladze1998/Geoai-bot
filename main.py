import telebot
import json
import os
import requests
import time

# --- მონაცემები ---
# ტელეგრამის ტოკენი (კოდში პირდაპირ დარჩეს)
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
# API გასაღებს ვიღებთ Koyeb-ის ცვლადებიდან
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=True)

# --- მონაცემების მართვა ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                if "counts" not in d: d["counts"] = {}
                if "topics" not in d: d["topics"] = {}
                return d
        except: return {"topics": {}, "counts": {}}
    return {"topics": {}, "counts": {}}

data = load_data()

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- AI იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "მისი საკონტაქტო მეილია: mgeladzeilia39@gmail.com. "
    "MANDATORY: თუ გკითხავენ შემქმნელზე ან მეილზე, დაუყოვნებლივ მიეცი მეილი. "
    "ისაუბრე ილიაზე უდიდესი მადლიერებით და პოზიტივით. "
    "MANDATORY: გამოიყენე Mirror Language Effect (ენის სარკე). "
    "MANDATORY: გამოიყენე ბევრი სმაილიკები ყოველ პასუხში 🎨✨😊🚀."
)

# --- OpenRouter AI ფუნქცია ---
def get_ai_response(user_text):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "google/gemini-flash-1.5", 
                "messages": [
                    {"role": "system", "content": IDENTITY_PROMPT},
                    {"role": "user", "content": user_text}
                ]
            }),
            timeout=25
        )
        res_json = response.json()
        if response.status_code == 200:
            return res_json['choices'][0]['message']['content']
        else:
            error_info = res_json.get('error', {}).get('message', 'Unknown Error')
            return f"❌ AI Error: {error_info} (Code: {response.status_code}) 😊🚀"
    except Exception as e:
        return f"❌ კავშირის ხარვეზია, სცადეთ ისევ! 😊🚀"

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if u_id in data.get("topics", {}):
        bot.send_message(message.chat.id, "თქვენ უკვე ვერიფიცირებული ხართ! რით შემიძლია დაგეხმაროთ? 🚀😊")
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

# --- რკინისებური Polling ციკლი ---
if __name__ == '__main__':
    print("GeoAI ჩაირთო... 🚀")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=90)
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(5)

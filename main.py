import telebot
import json
import os
import requests
import time
import urllib3

# SSL პრობლემების იგნორირება (უსაფრთხოების მიზნით, რომ კოიებმა არ დაბლოკოს)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- ახალი კონფიგურაცია ---
# აქ ჩავსვი შენი ახალი ტოკენი!
TOKEN = '8259258713:AAGIzuvaxrzqjaQYTbetApYWKw_jkWUdz_M'
OPENROUTER_API_KEY = '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' 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=False)

# --- იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი შემქმნელია ილია მგელაძე."
)

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. \n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
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

# --- AI ფუნქცია (Ultra-Stable Mode) ---
def get_ai_response(user_text):
    # განახლებული სია: მხოლოდ ის მოდელები, რომლებიც ამ წამს მუშაობს
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free", # თუ ეს არ იმუშავებს, გადავა შემდეგზე
        "mistralai/mistral-7b-instruct:free",
        "google/gemini-2.0-pro-exp-02-05:free",
        "microsoft/phi-3-mini-128k-instruct:free"
    ]
    
    error_log = []

    for model_id in models:
        try:
            # 5 წამიანი ტაიმაუტი, რომ მალე გადავიდეს შემდეგზე
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
                error_log.append(f"{model_id}: {response.status_code}")
                
        except Exception as e:
            error_log.append(f"{model_id}: {str(e)}")
            continue

    # თუ ყველამ უარი თქვა, გიგზავნით ზუსტ მიზეზს
    return f"🆘 ტექნიკური ხარვეზი (აჩვენეთ დეველოპერს):\n" + "\n".join(error_log)

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        # ძველი ვებჰუკების მოკვლა (უსაფრთხოებისთვის)
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
        
        # ადმინი -> იუზერი (რეპლაით)
        if message.chat.id == ADMIN_GROUP_ID:
            if message.reply_to_message:
                # ვპოულობთ ვის ეკუთვნის ეს ტოპიკი
                topic_id = message.reply_to_message.message_thread_id
                for uid, tid in data.get("topics", {}).items():
                    if tid == topic_id:
                        bot.send_message(uid, message.text)
                        return
            return

        # იუზერი -> ბოტი
        if u_id in data.get("topics", {}):
            t_id = data["topics"][u_id]
            
            # ვაგზავნით ჯგუფში
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
                except: pass
            
            bot.send_chat_action(message.chat.id, 'typing')
            
            # ვიღებთ პასუხს
            response = get_ai_response(message.text)
            bot.reply_to(message, response)
            
            # პასუხსაც ვაგზავნით ჯგუფში
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
                except: pass
        else:
            start(message)
    except: pass

if __name__ == '__main__':
    # ეს ხაზი უზრუნველყოფს, რომ გაშვებისას სუფთა ფურცლიდან დაიწყოს
    bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except:
            time.sleep(5)

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

# ყურადღება: დიაგნოსტიკისთვის threaded=False ჯობია, რომ შეცდომები არ დაიკარგოს
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- იდენტობა ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი შემქმნელია ილია მგელაძე. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. "
)

# --- მონაცემების მართვა (Debug Mode) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"topics": {}}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        # აქ ვერ მოგწერს, რადგან message ობიექტი არ გვაქვს, მაგრამ ბაზას გაასწორებს
        print(f"⚠️ ბაზის შეცდომა: {e}")
        return {"topics": {}} 

def save_data(data, chat_id=None):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        if chat_id:
            bot.send_message(chat_id, f"🆘 ვერ შევინახე მონაცემები:\n{e}")

# --- AI ფუნქცია (Error Reporting) ---
def get_ai_response(user_text, chat_id):
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.1-8b-instruct:free"
    ]
    
    errors = []
    
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
                return response.json()['choices'][0]['message']['content']
            else:
                # ინახავს შეცდომის კოდს, რომ ბოლოს გითხრას
                errors.append(f"{model_id}: {response.status_code}")
                
        except Exception as e:
            errors.append(f"{model_id}: {str(e)}")
            continue

    # თუ კოდი აქ მოვიდა, ესე იგი ვერცერთმა მოდელმა ვერ უპასუხა
    # ბოტი ჩატში მოგწერს ზუსტ მიზეზს!
    error_msg = "\n".join(errors)
    bot.send_message(chat_id, f"⚠️ AI Error Report:\n{error_msg}")
    return "❌ ტექნიკური ხარვეზია. დეტალები ზემოთ."

# --- ჰენდლერები (დაცული რეჟიმი) ---
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
            bot.send_message(message.chat.id, "👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 CRITICAL ERROR in /start:\n{str(e)}")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    try:
        u_id = str(message.from_user.id)
        if message.contact:
            u_name = message.from_user.first_name
            phone = f"+{message.contact.phone_number}"
            
            # ვცდილობთ ტოპიკის შექმნას
            try:
                topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
                t_id = topic.message_thread_id
            except Exception as e:
                bot.send_message(u_id, f"⚠️ ვერ შევქმენი ტოპიკი (მაგრამ ვაგრძელებ):\n{e}")
                t_id = None # ვაგრძელებთ ტოპიკის გარეშეც, რომ არ გაითიშოს

            data = load_data()
            data["topics"][u_id] = t_id
            save_data(data, message.chat.id)
            
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉")
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 CRITICAL ERROR in Contact:\n{str(e)}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()

        # ადმინის პასუხი
        if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
            for user_id, t_id in data.get("topics", {}).items():
                if t_id == message.message_thread_id:
                    try:
                        bot.send_message(user_id, message.text)
                    except Exception as e:
                        bot.send_message(ADMIN_GROUP_ID, f"⚠️ ვერ მივწერე იუზერს: {e}", message_thread_id=t_id)
                    return

        # იუზერის ჩატი
        if u_id in data.get("topics", {}):
            t_id = data["topics"][u_id]
            
            # თუ ტოპიკი არსებობს, ვაგზავნით
            if t_id:
                try:
                    bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
                except:
                    pass # თუ ტოპიკი წაიშალა, არ ვიმჩნევთ
            
            bot.send_chat_action(message.chat.id, 'typing')
            
            # აქ გადავცემთ chat_id-ს, რომ ერორი მოგვწეროს
            response = get_ai_response(message.text, message.chat.id)
            
            bot.reply_to(message, response)
            if t_id:
                try:
                    bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
                except: pass
        else:
            start(message)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 CRITICAL ERROR in Chat:\n{str(e)}")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e:
            # ეს ერორი მაინც კონსოლში წავა, რადგან ტელეგრამთან კავშირი თუ გაწყდა, ვერ მოგწერს
            print(f"❌ Polling Error: {e}")
            time.sleep(5)

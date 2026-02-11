import telebot
import json
import os
import requests
import time
import sys

# --- კონფიგურაცია ---
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
OPENROUTER_API_KEY = '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' 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

# ინიციალიზაცია
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
    "⚠️ **ყურადღება:** თქვენი მონაცემები და ჩატში გაზიარებული ინფორმაცია ხელმისაწვდომია ადმინისტრაციისთვის. "
    "ეს აუცილებელია უსაფრთხოებისთვის. \n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

# --- სისტემური ლოგერი (აგზავნის ჯგუფში) ---
def log_to_admin(text):
    """აგზავნის სისტემურ შეტყობინებას ადმინის ჯგუფში"""
    try:
        bot.send_message(ADMIN_GROUP_ID, f"🛠 **სისტემური ლოგი:**\n{text}")
    except:
        print(f"Log Error: {text}")

# --- მონაცემების მართვა ---
def load_data():
    if not os.path.exists(DATA_FILE): return {"topics": {}}
    try:
        with open(DATA_FILE, 'r') as f: return json.load(f)
    except: return {"topics": {}} 

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    except: pass

# --- AI ფუნქცია (დიაგნოსტიკით) ---
def get_ai_response(user_text):
    # განახლებული სია (სწორი სახელებით)
    models = [
        "google/gemini-2.0-flash-exp:free",      # ეს არის სწორი სახელი (არა lite-preview)
        "google/gemini-2.0-pro-exp-02-05:free",  # Pro ვერსია
        "mistralai/mistral-7b-instruct:free",    # Mistral
        "microsoft/phi-3-medium-128k-instruct:free" # Phi-3
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
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
            else:
                # ერორის კოდის დაფიქსირება
                errors.append(f"{model_id} -> {response.status_code}")
                
        except Exception as e:
            errors.append(f"{model_id} -> {str(e)}")
            continue

    # თუ ვერცერთმა ვერ უპასუხა, ლოგი მიდის ადმინთან
    error_report = "\n".join(errors)
    log_to_admin(f"⚠️ AI ვერ პასუხობს:\n{error_report}")
    return "❌ სერვერები გადატვირთულია. ტექნიკური ჯგუფი საქმის კურსშია. სცადეთ 30 წამში."

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()
        
        if u_id in data.get("topics", {}):
            bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀")
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
            bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        log_to_admin(f"Start Error: {e}")

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
            bot.send_message(u_id, "ახლა შეგიძლიათ მომწეროთ ნებისმიერი კითხვა! 🚀")
            log_to_admin(f"✅ ახალი მომხმარებელი: {u_name} ({phone})")
    except Exception as e:
        log_to_admin(f"Contact Error: {e}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()

        # ადმინის პასუხი
        if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
            for user_id, t_id in data.get("topics", {}).items():
                if t_id == message.message_thread_id:
                    try: bot.send_message(user_id, message.text)
                    except: log_to_admin(f"ვერ მივწერე იუზერს {user_id}")
                    return

        # იუზერის ჩატი
        if u_id in data.get("topics", {}):
            t_id = data["topics"][u_id]
            
            # ადმინთან
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
                except: pass
            
            bot.send_chat_action(message.chat.id, 'typing')
            
            # AI პასუხი
            response = get_ai_response(message.text)
            bot.reply_to(message, response)
            
            # AI პასუხი ადმინთან
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
                except: pass
        else:
            start(message)
            
    except Exception as e:
        log_to_admin(f"Chat Error: {e}")

if __name__ == '__main__':
    # 🔴 სუპერ მნიშვნელოვანი: ძველი კავშირების გაწყვეტა!
    try:
        print("Cleaning old webhooks...")
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
        log_to_admin("🚀 ბოტი გადაიტვირთა და მზადაა!")
    except Exception as e:
        print(f"Webhook error: {e}")

    # უსასრულო ციკლი დაცვით
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e:
            print(f"Critical Polling Error: {e}")
            time.sleep(5) # 5 წამი დასვენება კრახის შემდეგ

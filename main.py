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

# --- Privacy Policy ---
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. \n\n"
    "⚠️ **ყურადღება:** თქვენი მონაცემები და ჩატში გაზიარებული ინფორმაცია ხელმისაწვდომია ადმინისტრაციისთვის. "
    "ეს აუცილებელია მომსახურების ხარისხის და უსაფრთხოებისთვის. \n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

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

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- AI ფუნქცია (მხოლოდ API - ყველაზე სტაბილური) ---
def get_ai_response(user_text):
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
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
                timeout=8
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    return data['choices'][0]['message']['content']
            time.sleep(1)
        except: continue

    return "❌ სერვერები გადატვირთულია. სცადეთ 10 წამში! 😊🚀"

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    data = load_data()
    
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀😊\nშეგიძლიათ მომწეროთ ნებისმიერი კითხვა.")
    else:
        # აი, ეს აკლდა! ღილაკი და ვერიფიკაცია
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

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
            save_data(data)
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉😊")
        except: 
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია (ლოკალურად)! 🎉")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)
    data = load_data()

    # ადმინის პასუხი ჯგუფიდან
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data.get("topics", {}).items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # მომხმარებლის ჩატი
    if u_id in data.get("topics", {}):
        t_id = data["topics"][u_id]
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
        
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(message.text)
        
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
    else:
        # თუ უცხო გვწერს, ვთავაზობთ ვერიფიკაციას
        start(message)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except:
            time.sleep(5)

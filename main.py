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

# --- იდენტობა ✨ ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართული ხელოვნური ინტელექტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI'. "
    "შენი ერთადერთი შემქმნელია ილია მგელაძე. მასზე ისაუბრე მხოლოდ მაშინ, როცა გკითხავენ. "
    "ინფორმაცია ილიაზე: 27 წლის, გატაცებულია მუსიკით, პროგრამირებით, ჭეშმარიტების შეცნობით, ფილოსოფიით. "
    "ილიაზე ისაუბრე მადლიერებით, მაგრამ იყავი კონკრეტული და ნუ გადაიტან თემას სხვა რამეზე. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. "
    "გამოიყენე Mirror Language Effect და ბევრი სმაილიკები 🎨✨😊🚀."
)

# --- განახლებული Privacy Policy ადმინისტრაციის წვდომით ---
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. \n\n"
    "⚠️ **ყურადღება:** თქვენი პერსონალური მონაცემები და ჩატში გაზიარებული ნებისმიერი ინფორმაცია ხელმისაწვდომია ადმინისტრაციისთვის. "
    "ეს აუცილებელია მომსახურების ხარისხის გასაუმჯობესებლად, უსაფრთხოების მონიტორინგისთვის და ტექნიკური მხარდაჭერის უზრუნველსაყოფად. \n\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

# --- AI პასუხის ფუნქცია ---
def get_ai_response(user_text):
    models = ["google/gemini-2.0-flash-lite-preview-02-05:free", "meta-llama/llama-3.3-70b-instruct:free"]
    for model_id in models:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                data=json.dumps({
                    "model": model_id,
                    "messages": [{"role": "system", "content": IDENTITY_PROMPT}, {"role": "user", "content": user_text}]
                }),
                timeout=15
            )
            if response.status_code == 200: return response.json()['choices'][0]['message']['content']
        except: continue
    return "❌ სერვერი დროებით დაკავებულია. 😊🚀"

# --- ჰენდლერები ---

@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    if u_id in data["topics"]:
        bot.send_message(message.chat.id, "თქვენ უკვე ვერიფიცირებული ხართ! რით შემიძლია დაგეხმაროთ? 🚀😊")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, f"{PRIVACY_TEXT}\n\n👇 გაიარეთ ვერიფიკაცია:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    u_id = str(message.from_user.id)
    if message.contact and u_id not in data["topics"]:
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        try:
            # ტოპიკის შექმნა ადმინის ჯგუფში
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            data["topics"][u_id] = topic.message_thread_id
            data["counts"][u_id] = 0
            save_data()
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉😊")
        except:
            bot.send_message(u_id, "ხარვეზია ჯგუფში 😕")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # ადმინისტრატორის პასუხი ფორუმიდან
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, t_id in data["topics"].items():
            if t_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # მომხმარებლის შეტყობინება
    if u_id in data["topics"]:
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

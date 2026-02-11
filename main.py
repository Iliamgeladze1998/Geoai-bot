import telebot
import json
import os
import requests
import time
import urllib3

# უსაფრთხოების გაფრთხილების გათიშვა (Koyeb-ისთვის)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- ახალი ტოკენი ჩასმულია! ---
TOKEN = '8259258713:AAGIzuvaxrzqjaQYTbetApYWKw_jkWUdz_M'
OPENROUTER_API_KEY = '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' 
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN, threaded=False)

# --- იდენტობა (სრული ვერსია) ✨ ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართველი ასისტენტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე: 'მე მქვია GeoAI' 😊. "
    "შენი ერთადერთი შემქმნელია ილია მგელაძე. მასზე ისაუბრე მხოლოდ მაშინ, როცა გკითხავენ. "
    "ილიაზე ინფორმაცია: 27 წლისაა, გატაცებულია მუსიკით, პროგრამირებით, ჭეშმარიტების შეცნობით და ფილოსოფიით. ✨ "
    "ილიაზე ისაუბრე მადლიერებით და პოზიტივით. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com. "
    "STRICT RULE: არ გასცე სხვა პერსონალური ინფორმაცია ილიაზე! "
    "იყავი ადეკვატური, უპასუხე კონკრეტულად და გამოიყენე სმაილიკები 🎨✨😊🚀."
)

# --- Privacy Policy (სრული ვერსია) ---
PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. \n\n"
    "⚠️ **ყურადღება:** თქვენი მონაცემები და ჩატში გაზიარებული ინფორმაცია ხელმისაწვდომია ადმინისტრაციისთვის. "
    "ეს აუცილებელია მომსახურების ხარისხის გასაუმჯობესებლად და უსაფრთხოებისთვის. \n\n"
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
)

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

# --- AI ფუნქცია (განახლებული, მუშა მოდელებით) ---
def get_ai_response(user_text):
    # განახლებული სია (სწორი სახელებით, რომ 404 არ ამოაგდოს)
    models = [
        "google/gemini-2.0-flash-exp:free",      # ყველაზე სანდო Gemini ამ წუთას
        "mistralai/mistral-7b-instruct:free",    # ყველაზე სტაბილური ევროპული მოდელი
        "meta-llama/llama-3-8b-instruct:free",   # Meta-ს კლასიკა
        "microsoft/phi-3-medium-128k-instruct:free" # Microsoft backup
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
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
            else:
                errors.append(f"{model_id}: {response.status_code}")
                
        except Exception as e:
            continue

    # თუ ყველა მოდელმა უარი თქვა, მხოლოდ მაშინ გიგზავნის ერორს
    return f"❌ ყველა სერვერი დაკავებულია.\nდეტალები: {', '.join(errors)}"

# --- ჰენდლერები ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        # შლის ძველ ვებჰუკებს (409 ერორის პრევენცია)
        bot.delete_webhook(drop_pending_updates=True)
        
        u_id = str(message.from_user.id)
        data = load_data()
        
        if u_id in data.get("topics", {}):
            bot.send_message(message.chat.id, "GeoAI მზად არის! 🚀\nრით შემიძლია დაგეხმაროთ?")
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
            
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 🎉😊")
            # აქ არაფერს ვამატებთ ზედმეტს
    except: pass

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        u_id = str(message.from_user.id)
        data = load_data()
        
        # ადმინი -> იუზერი
        if message.chat.id == ADMIN_GROUP_ID:
            if message.reply_to_message:
                topic_id = message.reply_to_message.message_thread_id
                for uid, tid in data.get("topics", {}).items():
                    if tid == topic_id:
                        bot.send_message(uid, message.text)
                        return
            return

        # იუზერი -> ბოტი
        if u_id in data.get("topics", {}):
            t_id = data["topics"][u_id]
            
            # ადმინთან
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=t_id)
                except: pass
            
            bot.send_chat_action(message.chat.id, 'typing')
            
            response = get_ai_response(message.text)
            bot.reply_to(message, response)
            
            if t_id:
                try: bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=t_id)
                except: pass
        else:
            start(message)
    except: pass

if __name__ == '__main__':
    # გაშვებისას ვწმენდთ ძველ კავშირებს
    bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except:
            time.sleep(5)

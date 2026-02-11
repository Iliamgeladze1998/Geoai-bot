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

# --- ახალი, ადეკვატური იდენტობა ✨ ---
IDENTITY_PROMPT = (
    "შენი სახელია GeoAI. შენ ხარ მეგობრული ქართული ხელოვნური ინტელექტი. "
    "თუ გკითხავენ 'რა გქვია?', უპასუხე მოკლედ: 'მე მქვია GeoAI'. "
    "შენი შემქმნელია ილია მგელაძე. მასზე ისაუბრე მხოლოდ მაშინ, როცა გკითხავენ 'ვინ შეგქმნა?', 'ვინ არის ილია?' ან მსგავსს. "
    "ინფორმაცია ილიაზე: 27 წლისაა, აინტერესებს მუსიკა, პროგრამირება, ფილოსოფია და ჭეშმარიტების ძიება. "
    "ილიაზე საუბრისას იყავი მადლიერი და პოზიტიური, მაგრამ ნუ იქნები მომაბეზრებელი. "
    "საკონტაქტო მეილი: mgeladzeilia39@gmail.com (მიეცი მხოლოდ მოთხოვნისას). "
    "STRICT RULE: უპასუხე კონკრეტულად დასმულ კითხვას და ნუ გადაიტან თემას სხვა რამეზე! "
    "გამოიყენე Mirror Language Effect და ზომიერად სმაილიკები 🎨✨😊."
)

# --- AI ფუნქცია ---
def get_ai_response(user_text):
    models = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]
    for model_id in models:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://koyeb.com",
                    "X-Title": "GeoAI Bot"
                },
                data=json.dumps({
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": IDENTITY_PROMPT},
                        {"role": "user", "content": user_text}
                    ]
                }),
                timeout=15
            )
            res_json = response.json()
            if response.status_code == 200:
                return res_json['choices'][0]['message']['content']
            time.sleep(1)
        except: continue
    return "❌ სერვერი დროებით დაკავებულია. 😊🚀"

# --- დანარჩენი ჰენდლერები (უცვლელია) ---
@bot.message_handler(commands=['start'])
def start(message):
    u_id = str(message.from_user.id)
    bot.send_message(message.chat.id, "გამარჯობა! მე ვარ GeoAI. რით შემიძლია დაგეხმაროთ? 😊")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)
    # (აქ იგივე ლოგიკა დატოვე, რაც წინა კოდში გქონდა)
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_ai_response(message.text)
    bot.reply_to(message, response)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=90)
        except Exception:
            time.sleep(5)

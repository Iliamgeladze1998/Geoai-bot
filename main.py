import telebot
import json
import os
import requests

# --- კონფიგურაცია ---
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
# შენი OpenRouter გასაღები უკვე აქაა:
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
        except: return {"topics": {}, "phones": {}, "counts": {}}
    return {"topics": {}, "phones": {}, "counts": {}}

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

PRIVACY_TEXT = (
    "ℹ️ **კონფიდენციალურობის პოლიტიკა:**\n\n"
    "ბოტთან საუბრის დასაწყებად აუცილებელია ვერიფიკაცია. "
    "🛡️ ინფორმაცია არ გადაეცემა მესამე პირებს.\n\n"
    "✅ **ვერიფიკაციაზე დაჭერით ეთანხმებით პირობებს.**"
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
            # დიაგნოსტიკა: თუ რამე აირია, ბოტი გეტყვის მიზეზს
            error_info = res_json.get('error', {}).get('message', 'Unknown Error')
            return f"❌ AI Error: {error_info} (Code: {response.status_code}) 😊🚀"
            
    except Exception as e:
        return f"❌ კავშირის ხარვეზია, სცადეთ ისევ! 😊🚀"

# --- ჰენდლერები ---
def send_stars_invoice(chat_id):
    prices = [telebot.types.LabeledPrice(label="GeoAI Support 🌟", amount=50)]
    try:
        bot.send_invoice(
            chat_id, "მხარდაჭერა 🌟", "მადლობა, რომ ეხმარებით GeoAI-ს განვითარებაში!",

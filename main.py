import telebot
import g4f
import json
import os

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 
DATA_FILE = 'bot_data.json'

bot = telebot.TeleBot(TOKEN)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return {"topics": {}, "phones": {}}
    return {"topics": {}, "phones": {}}

def save_data(d):
    with open(DATA_FILE, 'w') as f: json.dump(d, f)

data = load_data()

# 🔍 ეს ფუნქციაა მთავარი: ის ამოწმებს ჯგუფში რეალურად არის თუ არა ჩატი
def is_topic_really_there(u_id):
    if u_id not in data["topics"]:
        return False
    try:
        # ვცდილობთ ჩატის სახელის "განახლებას". თუ ჩატი წაშლილია, ტელეგრამი ეგრევე მოგვცემს ერორს.
        thread_id = data["topics"][u_id]
        phone = data["phones"].get(u_id, "N/A")
        bot.edit_forum_topic(ADMIN_GROUP_ID, thread_id, name=f"User {u_id[-4:]} ({phone})")
        return True
    except:
        # თუ აქ მოვიდა, ჩატი წაშლილია! ამიტომ ფაილიდანაც ვშლით იუზერს.
        if u_id in data["topics"]: del data["topics"][u_id]
        if u_id in data["phones"]: del data["phones"][u_id]
        save_data(data)
        return False

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = str(message.from_user.id)

    # 🛑 ყოველი მესიჯისას ბოტი ჯერ ჯგუფში ამოწმებს ჩატს
    if not is_topic_really_there(u_id):
        # თუ ჩატი არ არის, ვთხოვთ ვერიფიკაციას (და აღარაფერს ვუშვებთ General-ში)
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
        bot.send_message(message.chat.id, "საუბრის დასაწყებად გაიარე ვერიფიკაცია 👇", reply_markup=markup)
        return # 👈 ეს აჩერებს პროცესს

    # ✅ თუ ჩატი ნაპოვნია, მხოლოდ მაშინ გრძელდება AI პასუხი
    try:
        full_prompt = f"GeoAI ხარ. მომხმარებელი: {message.text}"
        response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
        bot.reply_to(message, response)
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}\n🤖 {response}", message_thread_id=data["topics"][u_id])
    except:
        bot.reply_to(message, "ხარვეზია 😊")

bot.polling(none_stop=True)

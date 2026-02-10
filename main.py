import telebot
import g4f

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594  # შენი ჯგუფის ID

bot = telebot.TeleBot(TOKEN)
user_topics = {} # ინახავს რომელი იუზერი რომელ Topic-შია

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
    bot.send_message(message.chat.id, "GeoAI - საუბრისთვის გაიარე ვერიფიკაცია 👇", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id = message.from_user.id
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        
        try:
            # ქმნის ახალ Topic-ს (პაპკას) ჯგუფში
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            user_topics[u_id] = topic.message_thread_id
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
            bot.send_message(ADMIN_GROUP_ID, f"✅ ახალი იუზერი: {u_name}", message_thread_id=user_topics[u_id])
        except Exception as e:
            print(f"Topic Error: {e}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = message.from_user.id

    # 1. ადმინის პასუხი Topic-იდან იუზერთან
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, thread_id in user_topics.items():
            if thread_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # 2. იუზერის მესიჯის გადაგზავნა ადმინთან
    if u_id not in user_topics:
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{message.from_user.first_name}")
            user_topics[u_id] = topic.message_thread_id
        except: pass

    if u_id in user_topics:
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=user_topics[u_id])
        
        # AI პასუხი
        try:
            response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": message.text}])
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=user_topics[u_id])
        except:
            bot.reply_to(message, "ხარვეზია 😊")
    else:
        bot.send_message(message.chat.id, "გაიარე ვერიფიკაცია /start")

print("SERVER: TOPICS ACTIVE")
bot.polling(none_stop=True)

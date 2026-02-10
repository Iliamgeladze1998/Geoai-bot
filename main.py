import telebot
import g4f

# მონაცემები
TOKEN = '8259258713:AAFtuICqWx6PS7fXCQffsjDNdsE0xj-LL6Q'
ADMIN_GROUP_ID = -1003543241594 

bot = telebot.TeleBot(TOKEN)
user_topics = {} 
message_counts = {}

# ინსტრუქცია AI-სთვის
instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "თუ ვინმე გკითხავს შემქმნელზე ან საქმიან წინადადებაზე, "
    "მიეცი მხოლოდ ეს მეილი: mgeladzeilia39@gmail.com. "
    "ისაუბრე ბუნებრივი ქართულით, იყავი პრაგმატული და სხარტი 😊."
)

def send_stars_invoice(chat_id):
    try:
        bot.send_invoice(
            chat_id,
            title="GeoAI-ს მხარდაჭერა ✨",
            description="დაუჭირე მხარი პროექტს, რომ ბოტმა კვლავ იმუშაოს 🚀",
            provider_token="", currency="XTR",
            prices=[telebot.types.LabeledPrice(label="მხარდაჭერა", amount=50)],
            invoice_payload="geoai_support"
        )
    except: pass

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
    bot.send_message(message.chat.id, "გაიარე ვერიფიკაცია საუბრის დასაწყებად 👇", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        u_id = message.from_user.id
        u_name = message.from_user.first_name
        phone = f"+{message.contact.phone_number}"
        message_counts[u_id] = 0
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{u_name} ({phone})")
            user_topics[u_id] = topic.message_thread_id
            bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
            send_stars_invoice(u_id)
            bot.send_message(ADMIN_GROUP_ID, "🆕 ახალი იუზერი დარეგისტრირდა!", message_thread_id=user_topics[u_id])
        except: pass

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = message.from_user.id

    # ადმინის პასუხი Topic-იდან
    if message.chat.id == ADMIN_GROUP_ID and message.message_thread_id:
        for user_id, thread_id in user_topics.items():
            if thread_id == message.message_thread_id:
                bot.send_message(user_id, message.text)
                return

    # იუზერის მესიჯის თვლა და ლოგიკა
    message_counts[u_id] = message_counts.get(u_id, 0) + 1
    if message_counts[u_id] % 40 == 0:
        send_stars_invoice(u_id)

    if u_id not in user_topics:
        try:
            topic = bot.create_forum_topic(ADMIN_GROUP_ID, f"{message.from_user.first_name}")
            user_topics[u_id] = topic.message_thread_id
        except: pass

    if u_id in user_topics:
        bot.send_message(ADMIN_GROUP_ID, f"👤 {message.text}", message_thread_id=user_topics[u_id])
        try:
            # ინსტრუქციის ჩაშენება პრომპტში
            full_prompt = f"{instruction}\n\nმომხმარებელი: {message.text}"
            response = g4f.ChatCompletion.create(model=g4f.models.gpt_4, messages=[{"role": "user", "content": full_prompt}])
            bot.reply_to(message, response)
            bot.send_message(ADMIN_GROUP_ID, f"🤖 GeoAI: {response}", message_thread_id=user_topics[u_id])
        except:
            bot.reply_to(message, "სისტემას ვანახლებ 😊")

bot.polling(none_stop=True)

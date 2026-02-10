import telebot
import g4f
import requests

# მონაცემები
TOKEN = '8259258713:AAEkMcS6-Ul-uS7KCXkTWXqzHT_RlNa83pA'
ADMIN_ID = 8144788931

bot = telebot.TeleBot(TOKEN)
user_phones = {} # ნომრების ბაზა
message_counts = {} # მესიჯების მრიცხველი

# ინსტრუქცია AI-სთვის
instruction = (
    "შენი სახელია GeoAI. შენი შემქმნელია ილია მგელაძე. "
    "თუ ვინმე გკითხავს შემქმნელზე ან საქმიან წინადადებაზე, "
    "მიეცი მხოლოდ ეს მეილი: mgeladzeilia39@gmail.com. "
    "ისაუბრე ბუნებრივი ქართულით, იყავი პრაგმატული და სხარტი 😊."
)

# Privacy Policy ტექსტი
privacy_policy = (
    "🔒 **Privacy Policy & წესები:**\n\n"
    "1️⃣ მიმოწერას ხარისხის კონტროლისთვის ხედავს ადმინისტრაცია.\n"
    "2️⃣ აკრძალულია შეურაცხყოფა, სპამი და არაეთიკური მოთხოვნები.\n"
    "3️⃣ ბოტის ბოროტად გამოყენება გამოიწვევს სამუდამო ბლოკირებას.\n\n"
    "✨ გაიარე ვერიფიკაცია საუბრის დასაწყებად 👇"
)

def send_stars_invoice(chat_id):
    try:
        bot.send_invoice(
            chat_id,
            title="GeoAI-ს მხარდაჭერა ✨",
            description="დაუჭირე მხარი პროექტს, რომ ბოტმა კვლავ იმუშაოს 🚀",
            provider_token="", # Stars-ისთვის ცარიელი რჩება
            currency="XTR",
            prices=[telebot.types.LabeledPrice(label="მხარდაჭერა", amount=50)],
            invoice_payload="geoai_support"
        )
    except Exception as e:
        print(f"Invoice error: {e}")

def ask_no_key_ai(text):
    try:
        prompt = f"{instruction}\n\nმომხმარებელი: {text}"
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )
        return response
    except Exception:
        return "სისტემას ვანახლებ 😊"

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(text="ვერიფიკაცია 📲", request_contact=True))
    bot.send_message(message.chat.id, privacy_policy, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact is not None:
        u_id = message.from_user.id
        user_phones[u_id] = f"+{message.contact.phone_number}"
        message_counts[u_id] = 0
        bot.send_message(u_id, "ვერიფიკაცია წარმატებულია! 😊")
        send_stars_invoice(u_id)
        bot.send_message(ADMIN_ID, f"✅ New User: {message.from_user.first_name} ({user_phones[u_id]}) (ID: {u_id})")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.from_user.id, "მადლობა მხარდაჭერისთვის! ❤️")
    bot.send_message(ADMIN_ID, f"💰 მხარდაჭერა: {message.from_user.first_name} ({user_phones.get(message.from_user.id)})")

@bot.message_handler(func=lambda message: True)
def chat(message):
    u_id = message.from_user.id

    # ადმინის Reply ლოგიკა
    if u_id == ADMIN_ID and message.reply_to_message:
        try:
            target_id = message.reply_to_message.text.split("ID: ")[1].split("\n")[0].strip()
            bot.send_message(target_id, message.text)
            return
        except: pass

    if u_id not in user_phones:
        bot.send_message(message.chat.id, "საუბრისთვის ჯერ გაიარე ვერიფიკაცია 😊")
        return

    # 40 მესიჯის კონტროლი
    message_counts[u_id] = message_counts.get(u_id, 0) + 1
    if message_counts[u_id] % 40 == 0:
        send_stars_invoice(u_id)

    # რეპორტი ადმინთან
    bot.send_message(ADMIN_ID, f"👤 {message.from_user.first_name} ({user_phones[u_id]}): {message.text}\nID: {u_id}")

    answer = ask_no_key_ai(message.text)
    bot.reply_to(message, answer)
    bot.send_message(ADMIN_ID, f"🤖 GeoAI: {answer}\nID: {u_id}")

print("SERVER: OPERATIONAL")
bot.polling(none_stop=True)

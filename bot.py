import telebot
from flask import Flask
import threading

API_TOKEN = '8306328481:AAEFUyQMdrRnLvC0XcWgWsav6dKXUwMLZpU'
ADMIN_ID = 6324825537  # apna telegram id yaha daalo

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}

valid_keys = {
    "KEY123": 7,
    "KEY456": 30,
    "KEY789": 365
}

def is_premium(user_id):
    data = user_data.get(user_id, {})
    return data.get("premium", False)

def can_redeem(user_id):
    data = user_data.get(user_id, {})
    if is_premium(user_id):
        return True
    return data.get("redeem_used", False) == False

from telebot import types

@app.route('/')
def home():
    return "I'm alive!", 200

@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Redeem")
    btn2 = types.KeyboardButton("Premium Activate")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Redeem")
def redeem_handler(message):
    user_id = message.from_user.id
    if can_redeem(user_id):
        bot.send_message(user_id, "Please enter your redeem details:")
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["waiting_redeem"] = True
    else:
        bot.send_message(user_id, "You have already used your redeem limit. Upgrade to premium for unlimited use.")

@bot.message_handler(func=lambda message: message.text == "Premium Activate")
def premium_handler(message):
    bot.send_message(message.chat.id, "Please enter your premium key:")

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})

    if data.get("waiting_redeem", False):
        bot.send_message(ADMIN_ID, f"Redeem request from {message.from_user.first_name} ({user_id}):\n{message.text}")
        user_data[user_id]["redeem_used"] = True
        user_data[user_id]["waiting_redeem"] = False
        bot.send_message(user_id, "Your redeem request has been sent to admin.")
        return

    if message.text in valid_keys:
        days = valid_keys[message.text]
        user_data[user_id]["premium"] = True
        user_data[user_id]["premium_days"] = days
        bot.send_message(user_id, f"Premium activated for {days} days!")
        return
    elif message.text.startswith("/genk") and user_id == ADMIN_ID:
        try:
            _, target_id, days = message.text.split()
            target_id = int(target_id)
            days = int(days)
            user_data[target_id] = user_data.get(target_id, {})
            user_data[target_id]["premium"] = True
            user_data[target_id]["premium_days"] = days
            bot.send_message(target_id, f"Premium activated by admin for {days} days!")
            bot.send_message(ADMIN_ID, f"Premium activated for user {target_id}")
        except:
            bot.send_message(ADMIN_ID, "Invalid usage. Use /genk <user_id> <days>")
        return

@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "You are not authorized.")
        return
    msg = message.text.replace('/broadcast', '').strip()
    if not msg:
        bot.send_message(ADMIN_ID, "Please provide a message to broadcast.")
        return
    for uid in user_data.keys():
        try:
            bot.send_message(uid, msg)
        except:
            pass
    bot.send_message(ADMIN_ID, "Broadcast sent!")

@bot.message_handler(commands=['reply'])
def reply_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "You are not authorized.")
        return
    try:
        _, target_id, *reply_text = message.text.split()
        target_id = int(target_id)
        reply_msg = " ".join(reply_text)
        bot.send_message(target_id, f"Admin: {reply_msg}")
        bot.send_message(ADMIN_ID, "Reply sent!")
    except:
        bot.send_message(ADMIN_ID, "Use: /reply <user_id> <message>")

if __name__ == "__main__":
    # Flask server thread
    threading.Thread(target=app.run, kwargs={"host":"0.0.0.0", "port":8000}).start()

    print("Bot started polling...")
    bot.infinity_polling()

import telebot
from flask import Flask, request
import os
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '6226493394:AAEeoJlWJIuiUZ-UQVTElKL0f61BG7_uCOA')
CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID', '-1002148215113')  # Replace with your private channel's ID
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return 'Webhook Error', 500

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Send me any file, and I will generate a download link for you.')

@bot.message_handler(content_types=['document', 'video', 'audio', 'photo'])
def handle_file(message):
    try:
        # Forward the file to the channel
        forwarded_message = bot.forward_message(CHANNEL_ID, message.chat.id, message.message_id)
        
        # Generate a link to the forwarded message
        link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{forwarded_message.message_id}"
        
        # Create an inline keyboard with the download button
        keyboard = telebot.types.InlineKeyboardMarkup()
        download_button = telebot.types.InlineKeyboardButton(text="Download File", url=link)
        keyboard.add(download_button)
        
        bot.reply_to(message, "Your file is ready for download:", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"File handling error: {str(e)}")
        bot.reply_to(message, "An error occurred while processing your file. Please try again.")

if __name__ == '__main__':
    app.debug = True
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f'https://telefiletolink.onrender.com/{TOKEN}')
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logging.error(f"Startup error: {str(e)}")

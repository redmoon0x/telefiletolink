import telebot
from flask import Flask, request, Response
import requests
import os
import logging
from telebot.apihelper import ApiTelegramException
from collections import OrderedDict
from time import time

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '6226493394:AAEeoJlWJIuiUZ-UQVTElKL0f61BG7_uCOA')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# File ID cache with 6-hour expiration
FILE_CACHE_EXPIRATION = 6 * 60 * 60  # 6 hours in seconds
file_cache = OrderedDict()

def add_to_cache(file_id, file_info):
    if len(file_cache) >= 1000:  # Limit cache size
        file_cache.popitem(last=False)
    file_cache[file_id] = (file_info, time() + FILE_CACHE_EXPIRATION)

def get_from_cache(file_id):
    if file_id in file_cache:
        file_info, expiration = file_cache[file_id]
        if time() < expiration:
            return file_info
        else:
            del file_cache[file_id]
    return None

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return 'Webhook Error', 500

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        file_info = get_from_cache(file_id)
        if file_info is None:
            file_info = bot.get_file(file_id)
            add_to_cache(file_id, file_info)

        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        
        return Response(response.iter_content(chunk_size=8192), 
                        content_type=response.headers['Content-Type'],
                        headers={
                            'Content-Disposition': f'attachment; filename={file_info.file_path.split("/")[-1]}'
                        })
    except ApiTelegramException as e:
        logging.error(f"Telegram API error: {str(e)}")
        return 'File not found or expired', 404
    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return 'Error downloading file', 500
    except Exception as e:
        logging.error(f"Unexpected error in download_file: {str(e)}")
        return 'Internal server error', 500

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Send me any file, and I will generate a download link for you.')

@bot.message_handler(content_types=['document', 'photo'])
def handle_file(message):
    try:
        if message.document:
            file = message.document
        elif message.photo:
            file = message.photo[-1]
        else:
            bot.reply_to(message, "Please send a document or photo.")
            return

        file_id = file.file_id
        file_info = bot.get_file(file_id)
        add_to_cache(file_id, file_info)
        
        download_link = f"https://telefiletolink.onrender.com/download/{file_id}"
        bot.reply_to(message, f"Here is your download link (valid for 6 hours): {download_link}")
    except Exception as e:
        logging.error(f"File handling error: {str(e)}")
        bot.reply_to(message, "An error occurred while processing your file.")

if __name__ == '__main__':
    app.debug = True
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f'https://telefiletolink.onrender.com/{TOKEN}')
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logging.error(f"Startup error: {str(e)}")

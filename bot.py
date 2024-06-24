import telebot
from flask import Flask, request, Response
import requests

TOKEN = '6226493394:AAEeoJlWJIuiUZ-UQVTElKL0f61BG7_uCOA'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Telegram bot webhook endpoint
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200  # Return an empty string instead of '!'

# Route to handle file downloads
@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    file_info = bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    
    # Stream the file directly to the user
    response = requests.get(file_url, stream=True)
    response.raise_for_status()
    
    return Response(response.iter_content(chunk_size=8192), 
                    content_type=response.headers['Content-Type'],
                    headers={
                        'Content-Disposition': f'attachment; filename={file_info.file_path.split("/")[-1]}'
                    })

# Handle /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Send me any file, and I will generate a download link for you.')

# Handle documents and photos
@bot.message_handler(content_types=['document', 'photo'])
def handle_file(message):
    if message.document:
        file = message.document
    elif message.photo:
        file = message.photo[-1]
    else:
        bot.reply_to(message, "Please send a document or photo.")
        return

    file_id = file.file_id
    download_link = f"https://your-app-name.onrender.com/download/{file_id}"
    bot.reply_to(message, f"Here is your download link: {download_link}")

if __name__ == '__main__':
    # Remove existing webhook (if any) and set a new one
    bot.remove_webhook()
    bot.set_webhook(url=f'https://telefiletolink.onrender.com/{TOKEN}')
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000)

import telebot
from telebot import types
bot = telebot.TeleBot('7939672090:AAFII-LokIhrpPUObg15PLjq8xjDmgOT0GE')
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет Садовод держи ссылку<3")
bot.infinity_polling()
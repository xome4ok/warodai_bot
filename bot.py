#!/usr/bin/env python3

import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
import requests
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

QUERY, PAGING = range(2)
WARODAI_API_URL = 'https://warodai.ru/api/v1/corpus/lookup/?keyword={}'
INFO = '''Это интерфейс для сайта warodai.ru
        Любое введенное слово будет искаться в русско-японском словаре.
        Переводить можно как с русского на японский, так и наоборот.
        /cancel - завершает диалог с ботом.
        /help - покажет этот текст.'''
PREV, NEXT = '<', '>'
NEW_WORD = 'New word'

def paginator(warodai_state, current_page, update):
    cursor = []
    if len(warodai_state) > 1:
        if current_page > 0:
            cursor.append(PREV)
        if current_page < len(warodai_state) - 1:
            cursor.append(NEXT)
    cursor.append(NEW_WORD)
    update.message.reply_text(warodai_state[current_page],
        reply_markup=ReplyKeyboardMarkup([cursor], one_time_keyboard=True),
        parse_mode=ParseMode.HTML
    )


def pretty_warodai_entries(j):
    return [e['article'] for e in j]


def start(bot, update):
    user = update.message.from_user
    logger.info("User {} started the conversation.".format(user))
    update.message.reply_text(INFO)
    return QUERY


def help(bot, update):
    update.message.reply_text(INFO)


def warodai(bot, update, user_data):
    logger.info("Got request: {}".format(update.message.text))
    resp = requests.get(WARODAI_API_URL.format(update.message.text), verify=False)
    user_data['warodai_state'] = pretty_warodai_entries(resp.json())
    if not user_data['warodai_state']:
        update.message.reply_text('По запросу "{}" ничего не найдено.'.format(update.message.text))
        return QUERY
    user_data['current_page'] = 0
    paginator(user_data['warodai_state'], user_data['current_page'], update)
    return PAGING


def paging(bot, update, user_data):
    msg = update.message.text
    if msg == PREV:
        user_data['current_page'] -= 1
    elif msg == NEXT:
        user_data['current_page'] += 1
    elif msg == NEW_WORD:
        return QUERY

    paginator(user_data['warodai_state'], user_data['current_page'], update)
    return PAGING 


def error(bot, update, error):
    logger.warn('Update "{}" caused error "{}"'.format(update, error))


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User {} canceled the conversation.".format(user))
    update.message.reply_text('Bye!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main(argv):
    logger.info("Starting...")
    updater = Updater(argv[1])

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)], 
        states={
            QUERY: [MessageHandler(Filters.text, warodai, pass_user_data=True)],
            PAGING: [RegexHandler('^({}|{}|{})$'.format(PREV, NEXT, NEW_WORD), paging, pass_user_data=True)]
        }, 
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    logger.info("Started.")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main(sys.argv)
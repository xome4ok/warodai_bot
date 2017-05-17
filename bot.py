#!/usr/bin/env python3

import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
import requests
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

QUERY, PAGING = range(3)
WARODAI_API_URL = 'https://warodai.ru/api/v1/corpus/lookup/?keyword={}'


def paginator(warodai_state, current_page, update):
    cursor = []
    if len(warodai_state) > 1:
        if current_page > 0:
            cursor.append('Prev')
        if current_page < len(warodai_state) - 1:
            cursor.append('Next')
    cursor.append('New word')
    update.message.reply_text(warodai_state[current_page],
        reply_markup=ReplyKeyboardMarkup([cursor], one_time_keyboard=True),
        parse_mode=ParseMode.HTML
    )


def pretty_warodai_entries(j):
    return [e['article'] for e in j]


def start(bot, update):
    user = update.message.from_user
    logger.info("User %s started the conversation." % user.first_name)
    update.message.reply_text('hi!')
    return QUERY


def help(bot, update):
    update.message.reply_text('Help!')


def warodai(bot, update, user_data):
    resp = requests.get(WARODAI_API_URL.format(update.message.text), verify=False)
    user_data['warodai_state'] = pretty_warodai_entries(resp.json())
    if not user_data['warodai_state']:
        update.message.reply_text('Nothing found for {}'.format(update.message.text))
        return QUERY
    user_data['current_page'] = 0
    paginator(user_data['warodai_state'], user_data['current_page'])
    return PAGING


def paging(bot, update, user_data):
    msg = update.message.text
    if msg == 'Prev':
        user_data['current_page'] -= 1
    elif msg == 'Next':
        user_data['current_page'] += 1
    elif msg == 'New word':
        return QUERY

    paginator(user_data['warodai_state'], user_data['current_page'])
    return PAGING 


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Bye!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main(argv):
    updater = Updater(argv[1])

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)], 
        states={
            QUERY: [MessageHandler(Filters.text, warodai, pass_user_data=True)],
            PAGING: [RegexHandler('^(Next|Prev|New word)$', paging, pass_user_data=True)]
        }, 
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main(sys.argv)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import yaml
import actions as action
from imset import load_imsets
from objectdict import ObjectDict

no_keyboard = ReplyKeyboardRemove()
action_keyboard = ReplyKeyboardMarkup([['/make', '/guess']], resize_keyboard=True)

with open('config.yaml') as f:
  config = yaml.load(f, Loader=yaml.FullLoader)
  config['keyboard'] = {
    'action': action_keyboard,
    'empty': no_keyboard
  }
  config = ObjectDict(config)
  load_imsets(config)
action.use_config(config)

updater = Updater(token=config.token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
action_dict = {
  'start': action.start,
  'help': action.help,
  'team': action.team,
  'name': action.name,
  'stat': action.stat,
  'make': action.make,
  'guess': action.guess
}
for name, func in action_dict.items():
  dispatcher.add_handler(CommandHandler(name, func))

def text_back(update, context):
  if context.chat_data.get('make'):
    action.make_answer(update, context)
  elif context.chat_data.get('guess'):
    action.guess_answer(update, context)

text_handler = MessageHandler(Filters.text, text_back)
dispatcher.add_handler(text_handler)

updater.start_polling()


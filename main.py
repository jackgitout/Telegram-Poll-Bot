import logging
import Constants as keys
import Responses as R
from telegram import (
  Update
)
from telegram.constants import ParseMode
from telegram.ext import *
from datetime import datetime, timedelta

print ('Bot started...')

logging.basicConfig(
  format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level = logging.INFO
)

mute = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(
    chat_id = retrieve_chat_id(update),
    text = "I'm a bot, now ready to take training attendance!\n" +
    "/poll: generate poll\n" +
    "/mute: generate annoucements for updates to latest poll\n" +
    "/unmute: stop announcements for updates to latest poll"
  )

  store_chat_id(update, context)

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
  questions = keys.OPTIONS.split(', ')
  chat_id = retrieve_chat_id(update)
  message = await context.bot.send_poll(
    chat_id,
    f"[Week of {next_weekday(datetime.now(), 0)}] Training/scrim/pickup - vote for all that you'll show up for",
    questions,
    is_anonymous=False,
    allows_multiple_answers=True,
  )
  # Save some info about the poll the bot_data for later use in receive_poll_answer
  payload = {
    message.poll.id: {
      'questions': questions,
      'message_id': message.message_id,
      'chat_id': chat_id
    }
  }
  context.bot_data.update(payload)

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    global mute

    if not mute:
      answer = update.poll_answer
      try:
        answered_poll = context.bot_data[answer.poll_id]
      except KeyError:
        chat_id = retrieve_chat_id(update, context)
        await context.bot.send_message(
          chat_id,
          f"{update.effective_user.mention_html()} just made changes",
          parse_mode=ParseMode.HTML
        )
        return

      # looks at bot_data for latest poll id
      # only allow poll updates for the latest poll
      if answer.poll_id != latest_poll_id(context.bot_data):
          return
      else:
          questions = answered_poll['questions']

      selected_options = answer.option_ids
      answer_string = ''
      for question_id in selected_options:
        if question_id != selected_options[-1]:
          answer_string += questions[question_id] + ' and '
        else:
          answer_string += questions[question_id]

      if answer_string == '':
        response_msg = f"{update.effective_user.mention_html()} retracted previous votes"
      else:
        response_msg = f"{update.effective_user.mention_html()} just polled for {answer_string}"

      await context.bot.send_message(
        answered_poll['chat_id'],
        response_msg,
        parse_mode=ParseMode.HTML
    )

async def unmute_bot(update, context):
  global mute
  mute = False

  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text='I am now unmuted, will update player poll responses'
  )

async def mute_bot(update, context):
  global mute
  mute = True

  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text='I am now muted, will stop updating player poll responses'
  )

async def handle_message(update, context):
  text = str(update.message.text).lower()
  response = R.sample_responses(text)

  await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

async def aware(update, context):
  # function is used to support updates when polls are initialized when bot was offline
  store_chat_id(update, context)
  await context.bot.send_message(
    retrieve_chat_id(update),
    text='Done, stored chat_id'
  )

async def error(update, context):
  await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Update {update} caused error {context.error}")

def next_weekday(d, weekday):
  days_ahead = weekday - d.weekday()
  if days_ahead <= 0:  # Target day already happened this week
    days_ahead += 7
  return (d + timedelta(days_ahead)).strftime('%d-%b')

def latest_poll_id(bot_data):
  return max(list(bot_data))

def store_chat_id(update, context):
  chat_id = retrieve_chat_id(update)
  payload = {
    '0': {
      'chat_id': chat_id,
    }
  }
  context.bot_data.update(payload)

def retrieve_chat_id(update, context = None):
  if update.effective_chat:
    return update.effective_chat.id
  else:
    return context.bot_data['0']['chat_id']

if __name__ == '__main__':
    application = ApplicationBuilder().token(keys.API_KEY).build()

    # assign bot commands to code functions
    # /poll to async def poll
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('poll', poll))
    application.add_handler(CommandHandler('mute', mute_bot))
    application.add_handler(CommandHandler('unmute', unmute_bot))
    application.add_handler(CommandHandler('aware', aware))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_error_handler(error)
    application.run_polling()

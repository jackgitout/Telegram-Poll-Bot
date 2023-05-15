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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

mute = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, now ready to take training attendance!\n/poll: generate poll"
    )

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = keys.OPTIONS.split(', ')
    message = await context.bot.send_poll(
        update.effective_chat.id,
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
            'chat_id': update.effective_chat.id,
            'answers': 0,
        }
    }
    context.bot_data.update(payload)

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, mute_option: mute) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]

    if not mute:
      await context.bot.send_message(
          answered_poll["chat_id"],
          f"{update.effective_user.mention_html()} just polled!",
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

async def error(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Update {update} caused error {context.error}")

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return (d + timedelta(days_ahead)).strftime("%d-%b")

if __name__ == '__main__':
    application = ApplicationBuilder().token(keys.API_KEY).build()

    # assign bot commands to code functions
    # /poll to async def poll
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('poll', poll))
    application.add_handler(CommandHandler('mute', mute_bot))
    application.add_handler(CommandHandler('unmute', unmute_bot))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_error_handler(error)
    application.run_polling()

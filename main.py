import logging
import Constants as keys
import Responses as R
import Helpers as Helper
from telegram import (
  Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import *
from datetime import datetime
from random import choice

print ('Bot started...')

logging.basicConfig(
  format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level = logging.INFO
)

mute = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(
    chat_id=Helper.retrieve_chat_id(update),
    text="PE Class 🤖 at your service, ready to take training attendance!\n" +
         "/poll: to generate poll for upcoming training\n" +
         "/help: to find out more commands"
  )

  Helper.store_chat_id(update, context)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(
    chat_id = Helper.retrieve_chat_id(update),
    text = "Glad you asked, here is what I can do!\n" +
           "/poll: generate poll\n" +
           "/close: close the latest poll or a specific poll that is 'replied to'\n" +
           "/lines: pick the players in attendance and let me shuffle them into lines\n" +
           "/result: report the latest poll result or a specific poll that is 'replied to'\n" +
           "/mute: generate announcements for updates to latest poll\n" +
           "/unmute: stop announcements for updates to latest poll"
  )

  Helper.store_chat_id(update, context)

async def poll(update, context):
    # Create inline keyboard with Yes and No options
    keyboard = [
        [InlineKeyboardButton("Yes ✅", callback_data='yes')],
        [InlineKeyboardButton("No ⛔️", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user = update.effective_user
    alert_msg = Helper.greeting(user)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"{alert_msg} Starting a poll for the week of {Helper.next_weekday(datetime.now(), 2)}?", reply_markup=reply_markup)

async def lines(update, context):
    # Initialize the attendance list
    context.user_data['attendance'] = []

    # Create inline keyboard with Yes and No options
    keyboard = [
    ]

    for player in sorted(keys.PLAYERS.split(',')):
      keyboard.append([InlineKeyboardButton(f"{player}", callback_data=f"{player}")])

    keyboard.append([InlineKeyboardButton("Continue ✅", callback_data='continue')])
    keyboard.append([InlineKeyboardButton("Cancel ⛔️", callback_data='cancel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    user = update.effective_user
    alert_msg = Helper.greeting(user)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"{alert_msg} Picking lines?", reply_markup=reply_markup)

async def reshuffle_or_not(update, context, lines):
  # Save lines in user_data
  context.user_data['lines'] = lines

  # Send the final attendance message
  await context.bot.send_message(
    chat_id=Helper.retrieve_chat_id(update),
    text=f'Here are your lines'
  )
  await context.bot.send_message(
    chat_id=Helper.retrieve_chat_id(update),
    text=f"🌝 Lights {lines['Lights']}"
  )

  await context.bot.send_message(
    chat_id=Helper.retrieve_chat_id(update),
    text=f"🌑 Darks: {lines['Darks']}"
  )

  keyboard = [
    [InlineKeyboardButton("Yep, thanks ✅", callback_data='done')],
    [InlineKeyboardButton("Reshuffle pls 🔀 ", callback_data='reshuffle')]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await context.bot.send_message(chat_id=update.effective_chat.id,
                                  text=f"Happy with the lines?", reply_markup=reply_markup)

async def button_callback(update, context):
    query = update.callback_query
    text = query.message.text
    answer = query.data

    # Answer the callback query
    await query.answer()

    match Helper.type_of_request(text):
      # Create weekly poll
      case 1:
        if answer == 'yes':
          await create_poll(update, context)
        elif answer == 'no':
          await angry(update, context)
          angry_msg = choice(keys.ANGRY_RESPONSES.split(','))
          await context.bot.send_message(
            chat_id=Helper.retrieve_chat_id(update),
            text=angry_msg
          )

        await query.message.edit_reply_markup(
          reply_markup = None
        )
      # Pick lines
      case 2:
        attendance = context.user_data['attendance']

        if answer == 'cancel':
          await query.message.edit_reply_markup(
            reply_markup = None
          )
          await context.bot.send_message(
            chat_id=Helper.retrieve_chat_id(update),
            text=f"Bye!",
          )
        elif answer == 'continue':
          lines = Helper.split_lines(attendance)
          await query.message.edit_reply_markup(
            reply_markup = None
          )
          await reshuffle_or_not(update, context, lines)
        else:
          if answer in attendance:
            await context.bot.send_message(
              chat_id=Helper.retrieve_chat_id(update),
              text=f"{answer} already selected",
            )
          else:
            attendance.append(answer)
            await context.bot.send_message(
              chat_id=Helper.retrieve_chat_id(update),
              text=f"{answer} added to lines shuffle, anyone else?",
            )
      # Reshuffle lines
      case 3:
        if answer == 'done':
          pretty_lines = Helper.process_final_lines(context.user_data['lines'])

          await query.message.edit_reply_markup(
            reply_markup = None
          )

          await context.bot.send_message(
            chat_id=Helper.retrieve_chat_id(update),
            text=f"{pretty_lines}",
          )
        else:
          attendance = context.user_data['attendance']
          lines = Helper.split_lines(attendance)

          await query.message.edit_reply_markup(
            reply_markup = None
          )

          await reshuffle_or_not(update, context, lines)

async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
  chat_id = Helper.retrieve_chat_id(update)
  chat = await context.bot.get_chat(chat_id)
  week = f'[Week of {Helper.next_weekday(datetime.now(), 2)}]'
  question = f"{week} Training/scrim/pickup - vote for all that you'll show up for"

  if (chat.pinned_message and chat.pinned_message.from_user.first_name == 'pepoll') and chat.pinned_message.poll:
    if (chat.pinned_message.poll.question and chat.pinned_message.poll.question == question):
      await context.bot.send_message(
        chat_id,
        text= f'Hang on, there is already an existing poll for {week}'
      )
      await angry(update, context)
      return

  options = keys.OPTIONS.split(', ')
  message = await context.bot.send_poll(
    chat_id,
    question,
    options,
    is_anonymous=False,
    allows_multiple_answers=True,
  )
  # always try to unpin previous poll to prevent unreliabile results fetching
  if chat.pinned_message:
    await context.bot.unpin_chat_message(
      chat_id,
      chat.pinned_message.message_id
    )

  await context.bot.pin_chat_message(
    chat_id,
    message.message_id
  )
  if keys.ANNOUCEMENT:
    await context.bot.send_message(
      chat_id,
      text = keys.ANNOUCEMENT
    )

  # Save some info about the poll the bot_data for later use in receive_poll_answer
  payload = {
    message.poll.id: {
      'questions': options,
      'message_id': message.message_id,
      'chat_id': chat_id
    }
  }
  context.bot_data.update(payload)

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
  chat_id = Helper.retrieve_chat_id(update)
  message_id = Helper.retrieve_message_id(update, context)

  # if unable to retrieve message_id, bot will look at pinned message for final reference
  if not message_id:
    chat = await context.bot.get_chat(chat_id)
    if chat.pinned_message.from_user.is_bot == True and chat.pinned_message.poll:
      results = Helper.process_poll_results(chat.pinned_message.poll.options)

      await context.bot.send_message(
        chat_id,
        f"Here's the latest poll result for {Helper.extract_training_week(chat.pinned_message.poll.question)}" +
        f"{results}",
        parse_mode=ParseMode.HTML
      )
  else:
    results = Helper.process_poll_results(update.message.reply_to_message.poll.options)
    question = update.message.reply_to_message.poll.question

    await context.bot.send_message(
      chat_id,
      f"{question}" +
      f"{results}",
      parse_mode=ParseMode.HTML
    )

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    global mute

    if not mute:
      answer = update.poll_answer
      try:
        answered_poll = context.bot_data[answer.poll_id]
      except KeyError:
        try:
          chat_id = Helper.retrieve_chat_id(update, context)
        except KeyError:
          return

        await context.bot.send_message(
          chat_id,
          f"{update.effective_user.mention_html()} just made changes",
          parse_mode=ParseMode.HTML
        )
        return

      # looks at bot_data for latest poll id
      # only allow poll updates for the latest poll
      if answer.poll_id != Helper.latest_poll_id(context.bot_data):
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

  if not response == '':
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

async def monitor(update, context):
  # function is used to support updates when polls are initialized when bot was offline
  global mute
  mute = False

  Helper.store_chat_id(update, context)
  await context.bot.send_message(
    Helper.retrieve_chat_id(update),
    text='I will be reporting changes to attendance 🧐'
  )

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
  chat_id = Helper.retrieve_chat_id(update)
  message_id = Helper.retrieve_message_id(update, context)

  # if unable to retrieve message_id, bot will look at pinned message for final reference
  if not message_id:
    chat = await context.bot.get_chat(chat_id)
    if chat.pinned_message.from_user.is_bot == True and chat.pinned_message.poll:
      message_id = chat.pinned_message.message_id

  # closing a poll will unpin the poll and annouce results
  if message_id:
    message = await context.bot.stop_poll(
      chat_id,
      message_id
    )

    await context.bot.unpin_chat_message(
      chat_id,
      message_id
    )

    results = Helper.process_poll_results(message.options)
    await context.bot.send_message(
      chat_id,
      f"Poll is now closed for {Helper.extract_training_week(message.question)}!" +
      f"{results}"
    )

async def angry(update: Update, context: ContextTypes.DEFAULT_TYPE):
   sticker_file_id = keys.ANGRY_GIF

   await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_file_id)

if __name__ == '__main__':
    application = ApplicationBuilder().token(keys.API_KEY).build()

    # assign bot commands to code functions
    # /poll to async def poll
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('poll', poll))
    application.add_handler(CommandHandler('lines', lines))
    application.add_handler(CommandHandler('close', close))
    application.add_handler(CommandHandler('result', result))
    application.add_handler(CommandHandler('mute', mute_bot))
    application.add_handler(CommandHandler('unmute', unmute_bot))
    application.add_handler(CommandHandler('monitor', monitor))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('angry', angry))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.run_polling()

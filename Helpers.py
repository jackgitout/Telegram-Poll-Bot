from datetime import timedelta

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

def retrieve_chat_id(update, context=None):
  if update.effective_chat:
    return update.effective_chat.id
  else:
    try:
      return context.bot_data['0']['chat_id']
    except KeyError:
      raise KeyError('Unable to retrieve chat_id')

def retrieve_message_id(update, context):
  try:
    return update.effective_message.reply_to_message.message_id
  except AttributeError:
    try:
      poll_id = latest_poll_id(context.bot_data)
      return context.bot_data[poll_id]['message_id']
    except ValueError:
      return None

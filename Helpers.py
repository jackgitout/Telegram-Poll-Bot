from datetime import timedelta
import Constants as keys
import re

def next_weekday(d, weekday):
  days_ahead = weekday - d.weekday()
  if days_ahead <= 0:  # Target day already happened this week
    days_ahead += 7
  return (d + timedelta(days_ahead)).strftime('%d-%b')

def latest_poll_id(bot_data):
  return max(list(bot_data))

def store_chat_id(chat_id, context):
  payload = {
      '0': {
          'chat_id': chat_id
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
  # bot will access if there is a reply_to_message involved
  try:
    return update.effective_message.reply_to_message.message_id
  except AttributeError:
    # if not bot will retrieve the message_id from stored data
    try:
      poll_id = latest_poll_id(context.bot_data)
      return context.bot_data[poll_id]['message_id']
    except ValueError:
      return None

def process_poll_results(options):
  result_dict = {}
  for option in options:
    result_dict[option.text] = option.voter_count

  result = ''
  for key, value in dict(sorted(result_dict.items(), key=lambda x:x[1], reverse = True)).items():
    result += f"\n{key}: {value}"

  return result

def extract_training_week(question_str):
  pattern = "\[(.*)\]"
  return re.search(pattern, question_str).group()

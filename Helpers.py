from datetime import timedelta
import Constants as keys
import re
from random import choice, shuffle

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

def process_final_lines(lines):
  pretty_lines = ''

  for color, gender_players in lines.items():
    pretty_lines += '\n'
    pretty_lines += f"\n=={color}=="

    for gender, players in gender_players.items():
      pretty_lines += f"\n[{gender}]"

      for player in players:
        pretty_lines += f"\n{player}"

  return pretty_lines

def extract_training_week(question_str):
  pattern = "\[(.*)\]"
  return re.search(pattern, question_str).group()

def greeting(user):
  if user.username:
    if user.username in keys.DANGER_USERS:
      greeting = choice(keys.ESTEEMED_RESPONSES.split(','))
      return f"{greeting} {user.first_name}-sama 🙇‍♀️🙇🙇‍♂️"
    else:
        return f"Hey {user.first_name}!"
  else:
    return "Hey stranger_danger123!"

def type_of_request(text):
  if re.search(r"Starting a poll", text):
    return 1
  elif re.search(r"Picking lines", text):
    return 2
  elif re.search(r"Happy with the lines?", text):
    return 3

def split_lines(attendance):
  lights = {'M': [], 'F': []}
  darks = {'M': [], 'F': []}

  # Shuffle the attendance list to ensure randomness
  shuffle(attendance)

  for player in attendance:
    gender = player[-2]  # Assuming the gender is always at the 2nd position from the end

    name = re.sub(r'\s*\([MF]\)$', '', player)
    # Determine the key based on gender and availability
    if len(lights[gender]) <= len(darks[gender]):
      lights[gender].append(name)
    else:
      darks[gender].append(name)

  return {'Lights': lights, 'Darks': darks}

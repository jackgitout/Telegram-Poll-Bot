import requests
import Constants as keys

base_url = keys.API_BASE_URL + \
    f"consoles/{keys.INSTANCE_NAME}"
get_url = base_url + "/get_latest_output/"
post_url = base_url + "/send_input/"
headers = {
  'Authorization': f"Token {keys.API_TOKEN}"
}

def healthcheck_instance():
  try:
    response = requests.get(get_url, headers=headers)
    if response.status_code == 200:
      instance_data = response.json()

      if not 'Telegram' in instance_data['output']:
        data = {
            'input': "cd Telegram-Poll-Bot/\n nohup python3 main.py &\n"
        }
        input_response = requests.post(post_url, headers=headers, data=data)
        if input_response.status_code == 200:
            print("Input sent successfully.")
        else:
            print("Error sending input. Status code:", input_response.status_code)
    else:
      print("Error retrieving instance details. Status code:",
            response.status_code)
  except requests.exceptions.RequestException as e:
    print("Error connecting to the API:", str(e))

if __name__ == '__main__':
  healthcheck_instance()

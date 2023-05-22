# Setup

* Python Version 3.11

* Dependencies
  [Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot)

# Setting up a local repo
  
1. To get started with the app, first clone the repo and <code>cd</code> into the directory:
  
        $ gh repo clone jackgitout/Telegram-Poll-Bot
        $ cd Telegram-Poll-Bot

2. Install the necessary packages with pip (package installer for Python)

        
        $ pip install python-telegram-bot
        
3. [Set up a test bot with BotFather](https://core.telegram.org/bots/)
   
4. [Obtain bot token and create a secrets file `Constants.py` locally](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)
   
5. Add secrets to `Constants.py` file
        
        API_KEY = 'INSERT BOT TOKEN HERE'
        OPTIONS = 'POLLOPTION1, POLLOPTION2, POLLOPTION3, POLLOPTION4'

6. Run bot locally to test

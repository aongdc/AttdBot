from _._envs import *
from os import environ

DATABASE_PATH = './_data.sqlite3'
CRED_FILE = './_/_gcreds.json'
WORKBOOK_NAME = WORKBOOK_NAME
WORKBOOK_CODES_SHEETNAME = "Codes"
USERS_TXT = './_/_users.txt'
DATE_FORMAT = '%d/%m/%Y'
TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
PORT = int(environ.get('PORT', 5000))
WEB_ADDRESS = WEB_ADDRESS
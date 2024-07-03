import logging
import os
import sys
import time
from typing import List
import spamwatch
import telegram.ext as tg
from configparser import ConfigParser
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass

StartTime = time.time()


flag = """
\033[37m┌─────────────────────────────────────────────┐\033[0m\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│\n\033[37m│\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m  \033[0m\033[97;107m:::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│\n\033[37m│\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m  \033[0m\033[97;107m:::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│\n\033[37m│\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m  \033[0m\033[97;107m:::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│      \033[1mUnited we stand, Divided we fall\033[0m\n\033[37m│\033[97;107m:::::::::::::::::::::::::::::::::::::::::::::\033[0m\033[37m│ \033[1mKigyo Project, a tribute to USS Enterprise.\033[0m\n\033[37m│\033[91;101m#############################################\033[0m\033[37m│\n\033[37m│\033[97;107m:::::::::::::::::::::::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[91;101m#############################################\033[0m\033[37m│\n\033[37m│\033[97;107m:::::::::::::::::::::::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[91;101m#############################################\033[0m\033[37m│\n\033[37m└─────────────────────────────────────────────┘\033[0m\n
"""

parser = ConfigParser()
parser.read("config.ini")
ivoryconf = parser["ivoryconf"]

def get_user_list(key):
    # Import here to evade a circular import
    from tg_bot.modules.sql import nation_sql
    royals = nation_sql.get_royals(key)
    return [a.user_id for a in royals]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler('kigyo.log', maxBytes=1024*1024, backupCount=5), logging.StreamHandler()],
    level= ivoryconf.getboolean("IS_DEBUG", False) and logging.DEBUG or logging.WARN,
)

#print(flag)
log = logging.getLogger('[Enterprise]')
logging.getLogger('ptbcontrib.postgres_persistence.postgrespersistence').setLevel(logging.WARNING)
log.info("[KIGYO] Kigyo is starting. | An Eagle Union Project. | Licensed under GPLv3.")
log.info("[KIGYO] Not affiliated to Azur Lane or Yostar in any way whatsoever.")
log.info("[KIGYO] Project maintained by: github.com/Dank-del (t.me/dank_as_fuck)")

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 7:
    log.error(
        "[KIGYO] You MUST have a python version of at least 3.7! Multiple features depend on this. Bot quitting."
    )
    quit(1)

@dataclass
class IvoryINIT:
    def __init__(self, parser: ConfigParser):
        self.parser = parser
        self.SYS_ADMIN: int = self.parser.getint('SYS_ADMIN', 0)
        self.OWNER_ID: int = self.parser.getint('OWNER_ID')
        self.OWNER_USERNAME: str = self.parser.get('OWNER_USERNAME', None)
        self.APP_ID: str = self.parser.getint("APP_ID")
        self.API_HASH: str = self.parser.get("API_HASH")
        self.WEBHOOK: bool = self.parser.getboolean('WEBHOOK', False)
        self.URL: str = self.parser.get('URL', None)
        self.CERT_PATH: str = self.parser.get('CERT_PATH', None)
        self.PORT: int = self.parser.getint('PORT', None)
        self.INFOPIC: bool = self.parser.getboolean('INFOPIC', False)
        self.DEL_CMDS: bool = self.parser.getboolean("DEL_CMDS", False)
        self.STRICT_GBAN: bool = self.parser.getboolean("STRICT_GBAN", False)
        self.ALLOW_EXCL: bool = self.parser.getboolean("ALLOW_EXCL", False)
        self.CUSTOM_CMD: List[str] = ['/', '!']
        self.BAN_STICKER: str = self.parser.get("BAN_STICKER", None)
        self.TOKEN: str = self.parser.get("TOKEN")
        self.DB_URI: str = self.parser.get("SQLALCHEMY_DATABASE_URI")
        self.LOAD = self.parser.get("LOAD").split()
        self.LOAD: List[str] = list(map(str, self.LOAD))
        self.MESSAGE_DUMP: int = self.parser.getint('MESSAGE_DUMP', None)
        self.GBAN_LOGS: int = self.parser.getint('GBAN_LOGS', None)
        self.NO_LOAD = self.parser.get("NO_LOAD").split()
        self.NO_LOAD: List[str] = list(map(str, self.NO_LOAD))
        self.spamwatch_api: str = self.parser.get('spamwatch_api', None)
        self.CASH_API_KEY: str = self.parser.get('CASH_API_KEY', None)
        self.TIME_API_KEY: str = self.parser.get('TIME_API_KEY', None)
        self.WALL_API: str = self.parser.get('WALL_API', None)
        self.LASTFM_API_KEY: str = self.parser.get('LASTFM_API_KEY', None)
        self.CF_API_KEY: str =  self.parser.get("CF_API_KEY", None)
        self.bot_id = 0 #placeholder
        self.bot_name = "Kigyo" #placeholder
        self.bot_username = "KigyoRobot" #placeholder
        self.DEBUG: bool = self.parser.getboolean("IS_DEBUG", False)
        self.DROP_UPDATES: bool = self.parser.getboolean("DROP_UPDATES", True)
        self.BOT_API_URL: str = self.parser.get('BOT_API_URL', "https://api.telegram.org/bot")
        self.BOT_API_FILE_URL: str = self.parser.get('BOT_API_FILE_URL', "https://api.telegram.org/file/bot")
        self.SUPPORT_CHAT: str = self.parser.get('SUPPORT_CHAT', "codecarchive")

    def init_sw(self):
         if self.spamwatch_api is None:
             log.warning("SpamWatch API key is missing! Check your config.ini")
             return None
         else:
             try:
                 return spamwatch.Client(spamwatch_api)
             except Exception:
                 log.warning("Can't connect to SpamWatch!")
                 return None


lucido = IvoryINIT(parser=ivoryconf)

SYS_ADMIN = lucido.SYS_ADMIN
OWNER_ID = lucido.OWNER_ID
OWNER_USERNAME = lucido.OWNER_USERNAME
APP_ID = lucido.APP_ID
API_HASH = lucido.API_HASH
WEBHOOK = lucido.WEBHOOK
URL = lucido.URL
CERT_PATH = lucido.CERT_PATH
PORT = lucido.PORT
INFOPIC = lucido.INFOPIC
DEL_CMDS = lucido.DEL_CMDS
ALLOW_EXCL = lucido.ALLOW_EXCL
CUSTOM_CMD = lucido.CUSTOM_CMD
BAN_STICKER = lucido.BAN_STICKER
TOKEN = lucido.TOKEN
DB_URI = lucido.DB_URI
LOAD = lucido.LOAD
MESSAGE_DUMP = lucido.MESSAGE_DUMP
GBAN_LOGS = lucido.GBAN_LOGS
NO_LOAD = lucido.NO_LOAD
SUDO_USERS = [OWNER_ID] + get_user_list("sudos")
DEV_USERS = [OWNER_ID] + get_user_list("devs")
SUPPORT_USERS = get_user_list("supports")
SARDEGNA_USERS = get_user_list("sardegnas")
WHITELIST_USERS = get_user_list("whitelists")
SPAMMERS = get_user_list("spammers")
LOGGER = lucido.MESSAGE_DUMP
JOIN_LOGGER = lucido.MESSAGE_DUMP
spamwatch_api = lucido.spamwatch_api
CASH_API_KEY = lucido.CASH_API_KEY
TIME_API_KEY = lucido.TIME_API_KEY
WALL_API = lucido.WALL_API
LASTFM_API_KEY = lucido.LASTFM_API_KEY
CF_API_KEY = lucido.CF_API_KEY
sw = lucido.init_sw()
SUPPORT_CHAT = lucido.SUPPORT_CHAT

updater = tg.Updater(token=lucido.TOKEN, base_url=lucido.BOT_API_URL, base_file_url=lucido.BOT_API_FILE_URL, workers=min(100, os.cpu_count() + 16), request_kwargs={"read_timeout": 10, "connect_timeout": 10})
dispatcher = updater.dispatcher



# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD and len(CUSTOM_CMD) >= 1:
    tg.CommandHandler = CustomCommandHandler


def spamfilters(text, user_id, chat_id):
    # print("{} | {} | {}".format(text, user_id, chat_id))
    if int(user_id) not in SPAMMERS:
        return False

    print("This user is a spammer!")
    return True

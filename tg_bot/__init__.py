import logging
import os
import sys
import time
from typing import List
import spamwatch
import telegram.ext as tg
from configparser import ConfigParser
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field

StartTime = time.time()

flag = """
\033[37m┌─────────────────────────────────────────────┐\033[0m\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│\n\033[37m│\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m  \033[0m\033[97;107m:::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│\n\033[37m│\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m  \033[0m\033[97;107m:::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[44m\033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[97m★\033[0m\033[44m \033[0m\033[91;101m#########################\033[0m\033[37m│      \033[1mUnited we stand, Divided we fall\033[0m\n\033[37m│\033[97;107m:::::::::::::::::::::::::::::::::::::::::::::\033[0m\033[37m│ \033[1mKigyo Project, a tribute to USS Enterprise.\033[0m\n\033[37m│\033[91;101m#############################################\033[0m\033[37m│\n\033[37m│\033[97;107m:::::::::::::::::::::::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[91;101m#############################################\033[0m\033[37m│\n\033[37m│\033[97;107m:::::::::::::::::::::::::::::::::::::::::::::\033[0m\033[37m│\n\033[37m│\033[91;101m#############################################\033[0m\033[37m│\n\033[37m└─────────────────────────────────────────────┘\033[0m\n
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
    level=logging.DEBUG if ivoryconf.getboolean("IS_DEBUG", False) else logging.WARN,
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
    parser: ConfigParser
    SYS_ADMIN: int = field(init=False)
    OWNER_ID: int = field(init=False)
    OWNER_USERNAME: str = field(init=False)
    APP_ID: str = field(init=False)
    API_HASH: str = field(init=False)
    WEBHOOK: bool = field(init=False)
    URL: str = field(init=False)
    CERT_PATH: str = field(init=False)
    PORT: int = field(init=False)
    INFOPIC: bool = field(init=False)
    DEL_CMDS: bool = field(init=False)
    STRICT_GBAN: bool = field(init=False)
    ALLOW_EXCL: bool = field(init=False)
    CUSTOM_CMD: List[str] = field(default_factory=lambda: ['/', '!'])
    BAN_STICKER: str = field(init=False)
    TOKEN: str = field(init=False)
    DB_URI: str = field(init=False)
    LOAD: List[str] = field(init=False)
    MESSAGE_DUMP: int = field(init=False)
    GBAN_LOGS: int = field(init=False)
    NO_LOAD: List[str] = field(init=False)
    spamwatch_api: str = field(init=False)
    CASH_API_KEY: str = field(init=False)
    TIME_API_KEY: str = field(init=False)
    WALL_API: str = field(init=False)
    LASTFM_API_KEY: str = field(init=False)
    CF_API_KEY: str = field(init=False)
    bot_id: int = 0  # placeholder
    bot_name: str = "ivory"  # placeholder
    bot_username: str = "missivoryBot"  # placeholder
    bot: tg.Bot = field(init=False)
    update_queue: tg.UpdateQueue = field(init=False)
    dispatcher: tg.Dispatcher = field(init=False)
    updater: tg.Updater = field(init=False)
    spamwtc: spamwatch.Client = field(init=False)

    def __post_init__(self):
        ivory = self.parser["ivoryconf"]
        self.SYS_ADMIN = ivory.getint("SYS_ADMIN")
        self.OWNER_ID = ivory.getint("OWNER_ID")
        self.OWNER_USERNAME = ivory["OWNER_USERNAME"]
        self.APP_ID = ivory["APP_ID"]
        self.API_HASH = ivory["API_HASH"]
        self.WEBHOOK = ivory.getboolean("WEBHOOK")
        self.URL = ivory["URL"]
        self.CERT_PATH = ivory["CERT_PATH"]
        self.PORT = ivory.getint("PORT")
        self.INFOPIC = ivory.getboolean("INFOPIC")
        self.DEL_CMDS = ivory.getboolean("DEL_CMDS")
        self.STRICT_GBAN = ivory.getboolean("STRICT_GBAN")
        self.ALLOW_EXCL = ivory.getboolean("ALLOW_EXCL")
        self.BAN_STICKER = ivory["BAN_STICKER"]
        self.TOKEN = ivory["TOKEN"]
        self.DB_URI = ivory["SQLALCHEMY_DATABASE_URI"]
        self.LOAD = ivory["LOAD"].split()
        self.NO_LOAD = ivory["NO_LOAD"].split()
        self.MESSAGE_DUMP = ivory.getint("MESSAGE_DUMP")
        self.GBAN_LOGS = ivory.getint("GBAN_LOGS")
        self.spamwatch_api = ivory["SPAMWATCH_API"]
        self.CASH_API_KEY = ivory["CASH_API_KEY"]
        self.TIME_API_KEY = ivory["TIME_API_KEY"]
        self.WALL_API = ivory["WALL_API"]
        self.LASTFM_API_KEY = ivory["LASTFM_API_KEY"]
        self.CF_API_KEY = ivory["CF_API_KEY"]
        
        if self.spamwatch_api:
            self.spamwtc = spamwatch.Client(self.spamwatch_api)
        else:
            self.spamwtc = None

        persistence = tg.PicklePersistence(filepath="ivory")
        self.updater = tg.Updater(token=self.TOKEN, persistence=persistence, use_context=True)
        self.bot = self.updater.bot
        self.update_queue = self.updater.update_queue
        self.dispatcher = self.updater.dispatcher
        self.bot_id = self.bot.id
        self.bot_name = self.bot.first_name
        self.bot_username = self.bot.username

ivory = IvoryINIT(parser)
print(flag)

log.info("[IVORY] Telegraph Vars loaded.")

    # tg_bot import main
    #main()

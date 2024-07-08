import threading
from sqlalchemy import Column, String, UnicodeText, func, distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy import create_engine
from tg_bot import DB_URI, KInit, log

# Import CachingQuery from your previous script
from path.to.your.previous.script import CachingQuery

BASE = declarative_base()
DISABLE_INSERTION_LOCK = threading.RLock()
DISABLED = {}

class Disable(BASE):
    __tablename__ = "disabled_commands"
    chat_id = Column(String(14), primary_key=True)
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, command):
        self.chat_id = chat_id
        self.command = command

    def __repr__(self):
        return "Disabled cmd {} in {}".format(self.command, self.chat_id)

def start() -> scoped_session:
    try:
        engine = create_engine(DB_URI, echo=KInit.DEBUG)
        log.info("[MySQL] Connecting to database......")
        BASE.metadata.bind = engine
        BASE.metadata.create_all(engine, checkfirst=True)
        log.info("[MySQL] Database schema created or verified.")
        return scoped_session(
            sessionmaker(bind=engine, autoflush=False, query_cls=CachingQuery)
        )
    except Exception as e:
        log.exception(f"[MySQL] Failed to connect due to {e}")
        exit(1)

try:
    SESSION: scoped_session = start()
    log.info("[MySQL] Connection successful, session started.")
except Exception as e:
    log.exception(f"[MySQL] An error occurred: {e}")
    exit(1)

def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        disabled = SESSION.query(Disable).get((str(chat_id), disable))

        if not disabled:
            DISABLED.setdefault(str(chat_id), set()).add(disable)

            disabled = Disable(str(chat_id), disable)
            SESSION.add(disabled)
            SESSION.commit()
            return True

        SESSION.close()
        return False

def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        disabled = SESSION.query(Disable).get((str(chat_id), enable))

        if disabled:
            if enable in DISABLED.get(str(chat_id)):  # sanity check
                DISABLED.setdefault(str(chat_id), set()).remove(enable)

            SESSION.delete(disabled)
            SESSION.commit()
            return True

        SESSION.close()
        return False

def is_command_disabled(chat_id, cmd):
    return str(cmd).lower() in DISABLED.get(str(chat_id), set())

def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())

def num_chats():
    try:
        return SESSION.query(func.count(distinct(Disable.chat_id))).scalar()
    finally:
        SESSION.close()

def num_disabled():
    try:
        return SESSION.query(Disable).count()
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        chats = SESSION.query(Disable).filter(Disable.chat_id == str(old_chat_id)).all()
        for chat in chats:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)

        if str(old_chat_id) in DISABLED:
            DISABLED[str(new_chat_id)] = DISABLED.get(str(old_chat_id), set())

        SESSION.commit()

def __load_disabled_commands():
    global DISABLED
    try:
        all_chats = SESSION.query(Disable).all()
        for chat in all_chats:
            DISABLED.setdefault(chat.chat_id, set()).add(chat.command)
    finally:
        SESSION.close()

__load_disabled_commands()

from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from tg_bot import DB_URI, KInit, log

class CachingQuery(Query):
    """
    A subclass of Query that implements caching using the cache-aside caching pattern.
    """

    def __init__(self, *args, cache=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = cache or {}

    def __iter__(self):
        """
        Overrides the __iter__ method of the parent class to implement caching.
        """
        cache_key = self.cache_key()
        result = self.cache.get(cache_key)

        if result is None:
            result = list(super().__iter__())
            self.cache[cache_key] = result

        return iter(result)

    def cache_key(self):
        """
        Generates a cache key based on the query's SQL statement and parameters.
        """
        stmt = self.with_labels().statement
        compiled = stmt.compile()
        params = compiled.params
        return " ".join([str(compiled)] + [str(params[k]) for k in sorted(params)])

# Ensure the DB_URI is correctly set for MySQL
DB_URI = 'mysql://mysql:f417e82e0ee831fcfdef@104.251.216.208:9009/tg'

def start() -> scoped_session:
    try:
        engine = create_engine(DB_URI, echo=KInit.DEBUG)
        log.info("[MySQL] Connecting to database......")
        BASE.metadata.bind = engine
        BASE.metadata.create_all(engine)
        log.info("[MySQL] Database schema created or verified.")
        return scoped_session(
            sessionmaker(bind=engine, autoflush=False, query_cls=CachingQuery)
        )
    except Exception as e:
        log.exception(f"[MySQL] Failed to connect due to {e}")
        exit(1)

BASE = declarative_base()

class DisabledCommands(BASE):
    __tablename__ = 'disabled_commands'
    chat_id = Column(String(14), primary_key=True)
    command = Column(String(255), primary_key=True)

try:
    SESSION: scoped_session = start()
    log.info("[MySQL] Connection successful, session started.")
except Exception as e:
    log.exception(f"[MySQL] An error occurred: {e}")
    exit(1)

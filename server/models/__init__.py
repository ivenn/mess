from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session, sessionmaker


Base = declarative_base()
session = scoped_session(sessionmaker())


from server.models.user import User
from server.models.chat import Chat
from server.models.message import Message


def init_db(db='sqlite:///../mess.db', enable_logging=False):
    engine = create_engine(db,
                           echo=enable_logging  # enables sqlalchemy logging
                           )
    Base.metadata.bind = engine
    session.configure(bind=engine)
    Base.metadata.create_all(engine)

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
session = sessionmaker()


def init_db():
    engine = create_engine('sqlite:///../mess.db')
    Base.metadata.bind = engine
    session.configure(bind=engine)
    Base.metadata.create_all(engine)
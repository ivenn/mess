from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
session = sessionmaker()


def init_db(db='sqlite:///../mess.db', enable_logging=False):
    engine = create_engine(db,
                           echo=enable_logging  # enables sqlalchemy logging
                           )
    Base.metadata.bind = engine
    session.configure(bind=engine)
    Base.metadata.create_all(engine)

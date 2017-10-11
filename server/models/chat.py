import logging
import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, String, Table, UniqueConstraint
from sqlalchemy.orm import relationship

from server.models import Base


log = logging.getLogger(__name__)


chat_to_user = Table(
    'chat_to_user', Base.metadata,
    Column('chat_id', Integer, ForeignKey('chat.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    UniqueConstraint('chat_id', 'user_id', name='unique_participant'),
)


class Chat(Base):

    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    created_ts = Column(DateTime, default=datetime.datetime.utcnow)

    owner_id = Column(Integer, ForeignKey('user.id'))
    users = relationship("User",
                         secondary=chat_to_user,
                         back_populates="chats")

    def __init__(self, name, users=[]):
        self.name = name
        self.users = users


class ChatMessage(Base):

    __tablename__ = 'chat_message'

    id = Column(Integer, primary_key=True)
    created_ts = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text, nullable=False)

    chat_id = Column(Integer, ForeignKey('chat.id'))
    sent_by = Column(Integer, ForeignKey('user.id'))


class Message(Base):

    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    created_ts = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text, nullable=False)

    friendship_id = Column(Integer, ForeignKey('friendship.id'))
    sent_by = Column(Integer, ForeignKey('user.id'))

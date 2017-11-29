import logging
import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from server.models import Base


log = logging.getLogger(__name__)


# TODO: create base class for messages classes


class ChatMessage(Base):

    __tablename__ = 'chat_message'

    id = Column(Integer, primary_key=True)
    created_ts = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text, nullable=False)

    chat_id = Column(Integer, ForeignKey('chat.id'))
    chat = relationship('Chat', foreign_keys=[chat_id])

    sent_by = Column(Integer, ForeignKey('user.id'))
    by = relationship('User', foreign_keys=[sent_by, ])

    def __init__(self, data, chat, by):
        self.data = data
        self.chat = chat
        self.by = by

    def __repr__(self):
        return "ChatMessage(id={id}, ts={ts}, data={data}, chat={chat}, sent_by={sent_by})".format(
            id=self.id, ts=self.created_ts, data=self.data, chat=self.chat, sent_by=self.sent_by)


class Message(Base):

    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    created_ts = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text, nullable=False)

    to_id = Column(Integer, ForeignKey('user.id'))
    to = relationship('User', foreign_keys=[to_id, ])

    by_id = Column(Integer, ForeignKey('user.id'))
    by = relationship('User', foreign_keys=[by_id, ])

    def __init__(self, data, by, to):
        self.data = data
        self.to = to
        self.by = by

    def __repr__(self):
        return "Message(id={id}, ts={ts}, data={data}, to={to}, by={by})".format(
            id=self.id, ts=self.created_ts, data=self.data, by=self.by, to=self.to)
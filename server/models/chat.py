import logging
import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import relationship

from server.models import Base


log = logging.getLogger(__name__)


chat_to_user = Table(
    'chat_to_user', Base.metadata,
    Column('chat_id', Integer, ForeignKey('chat.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
)


class Chat(Base):

    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    created_ts = Column(DateTime, default=datetime.datetime.utcnow)

    owner_id = Column(Integer, ForeignKey('user.id'))
    owner = relationship('User')
    users = relationship('User',
                         secondary=chat_to_user,
                         back_populates='chats')

    def __init__(self, name, owner, users=[]):
        self.name = name
        self.owner = owner
        self.users = users

    def __repr__(self):
        return "Chat(id={id}, name={name}, owner={owner}, users={users})".format(id=self.id,
                                                                                 name=self.name,
                                                                                 owner=self.owner,
                                                                                 users=self.users)
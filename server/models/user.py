import logging
import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import UniqueConstraint, CheckConstraint, select
from sqlalchemy.orm import relationship

from server.models import Base
from server.models.chat import chat_to_user


log = logging.getLogger(__name__)


class Friendship(Base):

    __tablename__ = 'friendship'

    id = Column(Integer, primary_key=True)
    friend_a_id = Column(Integer, ForeignKey('user.id'))
    friend_b_id = Column(Integer, ForeignKey('user.id'))
    friend_a = relationship('User', foreign_keys=[friend_a_id, ])
    friend_b = relationship('User', foreign_keys=[friend_b_id, ])

    __table_args__ = (
        UniqueConstraint('friend_a_id', 'friend_b_id', name='unique_friendship'),
        CheckConstraint('NOT(friend_a_id == friend_b_id)', name='check_self_friend')
    )

    def __init__(self, friend_a, friend_b):
        self.friend_a = friend_a
        self.friend_b = friend_b

    def __repr__(self):
        return "Friendship({left}+{right})".format(left=self.friend_a, right=self.friend_b)


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    last_online_ts = Column(DateTime, default=datetime.datetime.utcnow)
    friends = relationship('User',
                           secondary=Friendship.__table__,
                           primaryjoin=id == Friendship.__table__.c.friend_a_id,
                           secondaryjoin=id == Friendship.__table__.c.friend_b_id,
                           back_populates='friends')
    chats = relationship('Chat',
                         secondary=chat_to_user,
                         back_populates='users')

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return "User(%s)" % self.name


# this relationship is viewonly and selects across the union of all friends
friendship_union = select([Friendship.__table__.c.friend_a_id,
                           Friendship.__table__.c.friend_b_id]).union(select([Friendship.__table__.c.friend_b_id,
                                                                              Friendship.__table__.c.friend_a_id])).alias()


User.all_friends = relationship('User',
                                secondary=friendship_union,
                                primaryjoin=User.id == friendship_union.c.friend_a_id,
                                secondaryjoin=User.id == friendship_union.c.friend_b_id,
                                viewonly=True)

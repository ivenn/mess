import logging

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, CheckConstraint, select
from sqlalchemy.orm import relationship

from server.models import Base
from server.models.chat import chat_to_user


log = logging.getLogger(__name__)


class Friendship(Base):

    __tablename__ = 'friendship'

    id = Column(Integer, primary_key=True)
    friend_a_id = Column(Integer, ForeignKey('user.id'))
    friend_b_id = Column(Integer, ForeignKey('user.id'))

    __table_args__ = (
        UniqueConstraint('friend_a_id', 'friend_b_id', name='unique_friendship'),
        CheckConstraint('NOT(friend_a_id == friend_b_id)', name='check_self_friend')
    )


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    friends = relationship('User',
                           secondary=Friendship.__table__,
                           primaryjoin=id == Friendship.__table__.c.friend_a_id,
                           secondaryjoin=id == Friendship.__table__.c.friend_b_id, )
    chats = relationship("Chat",
                         secondary=chat_to_user,
                         back_populates="users")

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

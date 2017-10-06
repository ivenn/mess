import logging

from sqlalchemy import Column, Integer, String, ForeignKey, Table, UniqueConstraint, CheckConstraint, select
from sqlalchemy.orm import relationship

from server.models import Base


log = logging.getLogger(__name__)


friendship = Table(
    'friendships', Base.metadata,
    Column('friend_a_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('friend_b_id', Integer, ForeignKey('user.id'), primary_key=True),
    UniqueConstraint('friend_a_id', 'friend_b_id', name='unique_friendship'),
    CheckConstraint('NOT(friend_a_id == friend_b_id)', name='check_self_friend')
)


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    friends = relationship('User',
                           secondary=friendship,
                           primaryjoin=id == friendship.c.friend_a_id,
                           secondaryjoin=id == friendship.c.friend_b_id, )

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return "User(%s)" % self.name


# this relationship is viewonly and selects across the union of all friends
friendship_union = select([friendship.c.friend_a_id,
                           friendship.c.friend_b_id]).union(select([friendship.c.friend_b_id,
                                                                    friendship.c.friend_a_id])).alias()


User.all_friends = relationship('User',
                                secondary=friendship_union,
                                primaryjoin=User.id == friendship_union.c.friend_a_id,
                                secondaryjoin=User.id == friendship_union.c.friend_b_id,
                                viewonly=True)

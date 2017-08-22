import logging

from sqlalchemy import Column, Integer, String
from server.models import Base
from server.messages import NormalMessage, CMD_CHANGE_STATUS


class InvalidUserCredentials(Exception):
    pass


class NoSuchUserOnline(Exception):
    pass


class UserAlreadyLoggedInException(Exception):
    pass


class UserIsNotLoggedInException(Exception):
    pass


log = logging.getLogger('user')


STATE_ONLINE = 'ONLINE'
STATE_OFFLINE = 'OFFLINE'


ONLINE_USERS = {}


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    password = Column(String(128), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password
        self._state = STATE_OFFLINE
        self.client = None

    def __repr__(self):
        return "User(%s)" % self.name

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state
        for user in ONLINE_USERS.values():
            user.client.send(NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.name, new_state]))

    def login(self, password, client):
        if self.password == password:
            ONLINE_USERS[self.name] = self
            self.client = client
            self.state = STATE_ONLINE
            log.info("{user} was logged in from {client}".format(user=self, client=client))
        else:
            raise InvalidUserCredentials()

    def logout(self):
        log.info("{user} logged out from {client}".format(user=self, client=self.client))
        del ONLINE_USERS[self.name]
        self.client = None
        self.state = STATE_OFFLINE

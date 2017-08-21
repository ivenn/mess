from sqlalchemy import Column, Integer, String
from server.models import Base


class InvalidUserCredentials(Exception):
    pass


class NoSuchUserOnline(Exception):
    pass


class UserAlreadyLoggedInException(Exception):
    pass


class UserIsNotLoggedInException(Exception):
    pass


ONLINE_USERS = {}


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    password = Column(String(128), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.client = None

    def __repr__(self):
        return "User(%s)" % self.name

    def login(self, password, client):
        if self.password == password:
            ONLINE_USERS[self.name] = self
            self.client = client
            print("%s was logged in from %s" % (self, client))
        else:
            raise InvalidUserCredentials()

    def logout(self):
        print("%s will be logged out from %s" % (self, self.client))
        del ONLINE_USERS[self.name]
        self.client = None


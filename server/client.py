import logging
from functools import wraps

from server.models import session
from server.models.user import User, UserAlreadyLoggedInException, InvalidUserCredentials, ONLINE_USERS
from server.messages import Message, NormalMessage

log = logging.getLogger('client')


class ClientIsNotLoggedInException(Exception):
    pass


class ClientIsAlreadyLoggedIn(Exception):
    pass


def login_required(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        client = args[0]

        if not client.logged_in:
            raise ClientIsNotLoggedInException()
        return func(*args, **kwargs)

    return wrapped


class Client:

    def __init__(self, conn):
        self.conn = conn
        self.user = None

    def __repr__(self):
        return "Client(%s:%s)" % (self.conn.getpeername()[0], self.conn.getpeername()[1])

    @property
    def logged_in(self):
        return self.user is not None

    def login_as(self, name, password):
        if self.logged_in:
            raise ClientIsAlreadyLoggedIn(self.user)
        user = session().query(User).filter(User.name == name).one()
        if user:
            if user.name in ONLINE_USERS:
                raise UserAlreadyLoggedInException(user.name)
            else:
                user.login(password, self)
                self.user = user
        else:
            raise InvalidUserCredentials()

    def send(self, msg):
        """
        @param msg: Message subclass instance or bytes or string
        """
        if type(msg) is str:
            msg = msg.encode('utf-8')
        if isinstance(msg, Message):
            msg = msg.as_bytes()
        self.conn.send(msg)
        log.info("{client} <<< {msg}".format(client=self, msg=msg))

    def status(self):
        if self.logged_in():
            return self.send("You are logged in")
        else:
            return self.send("You are not logged in!")

    @login_required
    def logout(self):
        self.user.logout()
        self.user = None


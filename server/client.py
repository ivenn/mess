import logging
from functools import wraps

from server.models import session
from server.models.user import User, UserAlreadyLoggedInException, InvalidUserCredentials, ONLINE_USERS
from server.messages import DataBuffer, DataParser, MessageDispatcher, CMD_LOGIN, CMD_LOGOUT, Message


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

    def __init__(self, conn, server=None):
        self.conn = conn
        self.user = None
        self.server = server
        self.data_buffer = DataBuffer()
        self.data_parser = DataParser()
        self.msg_dispatcher = MessageDispatcher()

    def __repr__(self):
        return "Client(%s:%s)" % (self.conn.getpeername()[0], self.conn.getpeername()[1])

    @property
    def logged_in(self):
        """
        Is client logged in or not
        """
        return self.user is not None

    def login_as(self, name, password):
        """
        Login client
        """
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

    def recv(self, data):
        """
        Receive bytes and handle them
        """
        log.info("{self} got: {data}".format(self=self, data=data))
        raw_messages = self.data_buffer.push(data)
        # if we got complete message lets handle it
        for raw_msg in raw_messages:
            msg = self.data_parser.parse(raw_msg)
            self.msg_dispatcher.dispatch(self, msg)

    def handle_normal_msg(self, msg):
        """
        Handles NormalMessages
        """
        if msg.cmd == CMD_LOGIN:
            if len(msg.params) != 2:
                raise InvalidUserCredentials()
            self.login_as(msg.params[0], msg.params[1])
        if msg.cmd == CMD_LOGOUT:
                self.logout()

    def handle_payload_msg(self, msg):
        """
        Handles PayloadMessages
        """
        raise NotImplementedError()

    def handle_error_msg(self, msg):
        """
        Handles ErrorMessages
        """
        raise NotImplementedError()

    def handle_service_msg(self, msg):
        """
        Handles ServiceMessages
        """
        raise NotImplementedError()

    def send(self, msg):
        """
        Sends Message or bytes to client
        @param msg: Message subclass instance or bytes or string
        """
        if type(msg) is str:
            msg = msg.encode('utf-8') + b'\n'
        if isinstance(msg, Message):
            msg = msg.as_bytes() + b'\n'
        self.conn.send(msg)
        log.info("{client} <<< {msg}".format(client=self, msg=msg))

    def status(self):
        """
        Sends client its status
        """
        if self.logged_in():
            return self.send("You are logged in")
        else:
            return self.send("You are not logged in!")

    @login_required
    def logout(self):
        """
        Logout client
        """
        self.user.logout()
        self.user = None

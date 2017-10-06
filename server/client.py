import logging
from functools import wraps

from server.models import session
from server.online import ONLINE_USERS
from server.models.user import User
from server.messages import DataBuffer, DataParser, Message
from server.messages import CMD_CHANGE_STATUS, CMD_INFO
from server.messages import NormalMessage, PayloadMessage
from server.dispatcher import MessageDispatcher


log = logging.getLogger('client')


class NoSuchStatusException(Exception):
    pass


class NoSuchUserException(Exception):
    pass


class InvalidUserCredentials(Exception):
    pass


class NoSuchFriendException(Exception):
    pass


class NoSuchUserOnlineException(Exception):
    pass


class UserAlreadyLoggedInException(Exception):
    pass


class UserIsNotLoggedInException(Exception):
    pass


class ClientIsNotLoggedInException(Exception):
    pass


class ClientIsAlreadyLoggedIn(Exception):
    pass

CLIENT_OFFLINE = 'OFFLINE'

USER_STATUS_DEFAULT = 'ONLINE'
USER_STATUS_BUSY = 'BUSY'
USER_STATUSES = [USER_STATUS_BUSY, USER_STATUS_DEFAULT]


def login_required(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        client = args[0]

        if not client.user:
            raise ClientIsNotLoggedInException()
        return func(*args, **kwargs)

    return wrapped


class Client:

    def __init__(self, conn, server=None):
        self.conn = conn
        self.server = server  # just to get debug info about server state
        self.__user = None
        self.__status = None
        self.data_buffer = DataBuffer()
        self.data_parser = DataParser()
        self.msg_dispatcher = MessageDispatcher()

    def __repr__(self):
        return "Client(%s:%s)" % (self.conn.getpeername()[0], self.conn.getpeername()[1])

    @property
    def info(self):
        return None

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, user):
        if isinstance(user, User):
            if self.__user:
                raise ClientIsAlreadyLoggedIn(self.__user)
            else:
                self.__user = user
                ONLINE_USERS[user.name] = self
                self.status = USER_STATUS_DEFAULT
        elif user is None:
            del ONLINE_USERS[self.user.name]
            self.status = None
            self.__user = None
        else:
            raise ValueError(user)

    @property
    def status(self):
        return self.__status if self.user else self.user

    @status.setter
    def status(self, new_status):
        if new_status in USER_STATUSES or new_status is None:
            self.__status = new_status
            status_msg = new_status if new_status else CLIENT_OFFLINE
            for friend_name in [u.name for u in self.user.all_friends if u.name in ONLINE_USERS]:
                client = ONLINE_USERS[friend_name]
                client.send(NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user.name, status_msg]))
        else:
            raise NoSuchStatusException(new_status)

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

    def send(self, msg):
        """
        Sends Message or bytes to client
        @param msg: Message subclass instance or bytes or string
        """
        if type(msg) is str:
            msg = msg.encode('utf-8')
        if isinstance(msg, Message):
            msg = msg.as_bytes()
        self.conn.send(msg)
        log.info("{client} <<< {msg}".format(client=self, msg=msg))

    def login_as(self, name, password):
        """
        Login client
        """
        if self.user:
            raise ClientIsAlreadyLoggedIn(self.user)
        user = session().query(User).filter(User.name == name).one()
        if user:
            if user.name in ONLINE_USERS:
                raise UserAlreadyLoggedInException(user.name)
            else:
                if user.password == password:
                    log.info("{user} was logged in from {client}".format(user=user, client=self))
                else:
                    raise InvalidUserCredentials()
                self.user = user
        else:
            raise InvalidUserCredentials()

    @login_required
    def logout(self):
        """
        Logout client
        """
        log.info("{user} logged out from {client}".format(user=self.user, client=self))
        self.user = None

    @login_required
    def get_friends(self, online_only=False):
        """
        Returns dict {friend's name: info}
        """
        res = {}
        for friend in self.user.all_friends:
            if friend.name in ONLINE_USERS:
                res[friend.name] = ONLINE_USERS[friend.name].status
            elif not online_only:
                res[friend.name] = CLIENT_OFFLINE
        self.send(PayloadMessage(CMD_INFO, [], res))

    @login_required
    def send_message_to(self, msg):
        # verify msg
        assert isinstance(msg, PayloadMessage)
        to = msg.params[0]
        # verify to
        user_to = session().query(User).filter(User.name == to).one()
        if not user_to:
            raise NoSuchUserException(to)
        if user_to.name not in [u.name for u in self.user.all_friends]:
            raise NoSuchFriendException(to)
        if user_to.name not in ONLINE_USERS:
            raise NoSuchUserOnlineException(to)

        # send msg
        ONLINE_USERS[to].send(PayloadMessage(msg.cmd, [self.user.name], msg.payload))

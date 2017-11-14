import logging
import socket

from server.online import ONLINE_USERS
from server.models.user import User

from protocol.messages import Message, NormalMessage, CMD_CHANGE_STATUS
from protocol.data_utils import DataBuffer, DataParser


log = logging.getLogger(__name__)


class ClientIsAlreadyLoggedInException(Exception):
    pass


class NoSuchStatusException(Exception):
    pass


CLIENT_OFFLINE = 'OFFLINE'

USER_STATUS_DEFAULT = 'ONLINE'
USER_STATUS_BUSY = 'BUSY'
USER_STATUSES = [USER_STATUS_BUSY,
                 USER_STATUS_DEFAULT]


class BaseClient:

    def __init__(self, conn, server=None):
        self.conn = conn
        self.server = server  # just to get debug info about server state
        self.__user = None
        self.__status = None
        self.data_buffer = DataBuffer()
        self.data_parser = DataParser()
        self.addr = "({ip}:{port})".format(ip=self.conn.getpeername()[0],
                                           port=self.conn.getpeername()[1])

    def __repr__(self):
        if self.user:
            return "Client({username})".format(username=self.user.name)
        else:
            return "Client({address})".format(address=self.addr)

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
                raise ClientIsAlreadyLoggedInException(self.__user)
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

    def handle(self, msg):
        raise NotImplementedError()

    def recv(self, data):
        """
        Receive bytes and handle them
        """
        log.info("{self} got: {data}".format(self=self, data=data))
        raw_messages = self.data_buffer.push(data)
        # if we got complete message lets handle it
        for raw_msg in raw_messages:
            msg = self.data_parser.parse(raw_msg)
            self.handle(msg)

    def send(self, msg):
        """
        Sends Message or bytes to client
        @param msg: Message subclass instance or bytes or string
        """
        if type(msg) is str:
            msg = msg.encode('utf-8')
        if isinstance(msg, Message):
            msg = msg.as_bytes()
        try:
            self.conn.send(msg)
        except BrokenPipeError:
            self.log.warning('BrokenPipeError - %s' % self.user.name)
            # TODO: clean all
        except ConnectionResetError as cre:
            log.warning(cre)
        log.info("{client} <<< {msg}".format(client=self, msg=msg))

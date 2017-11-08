from functools import wraps

from protocol.messages import CMD_LOGIN, CMD_LOGOUT, NormalMessage, Message
from protocol.data_utils import DataParser
from test.lib.client import TestClient


class NotConnectedException(Exception):
    pass


def connected(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        user = args[0]
        if not user.is_connected:
            raise NotConnectedException()
        else:
            return func(*args, **kwargs)

    return wrapped


class TestUser:

    def __init__(self, name, password, server_host='127.0.0.1', server_port=9090):
        self.name = name
        self.password = password
        self.client = None
        self.parcer = DataParser()
        self.server_host = server_host
        self.server_port = server_port
        self.__logged_in = False

    @property
    def is_connected(self):
        return self.client is not None

    @property
    def logged_in(self):
        return self.__loggedin

    def connect(self):
        self.client = TestClient()
        return self.client.connect(self.server_host, self.server_port)

    @connected
    def login(self):
        self.client.send(NormalMessage(cmd=CMD_LOGIN, params=[self.name, self.password]))
        self.__loggedin = True

    @connected
    def recv_msg(self, timeout=5):
        data = self.client.recv(timeout=timeout)
        data = data.split(Message.TERM_SEQUENCE)[0]
        msg = self.parcer.parse(data)

        return msg

    @connected
    def logout(self):
        self.client.send(NormalMessage(cmd=CMD_LOGOUT))
        self.__loggedin = False

    @connected
    def disconnect(self):
        self.client.disconnect()
        self.client = None

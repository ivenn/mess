import logging
from functools import wraps

from server.models import session
from server.models.user import User
from server.online import ONLINE_USERS

from server.base_client import BaseClient, CLIENT_OFFLINE, ClientIsAlreadyLoggedInException

from protocol.messages import CMD_INFO, CMD_LOGIN, CMD_LOGOUT, CMD_FRIENDS, CMD_MESSAGE
from protocol.messages import PayloadMessage


log = logging.getLogger(__name__)


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


class NoHandlerForCmdRegisteredException(Exception):
    pass


def login_required(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        client = args[0]

        if not client.user:
            raise ClientIsNotLoggedInException()
        return func(*args, **kwargs)

    return wrapped


def cmd_handler_cls(cls):

    cls.handlers = {}
    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method, '_registered_cmd'):
            cls.handlers.update({method._registered_cmd: methodname})

    return cls


def register_cmd(cmd):

    def wrapper(func):
        func._registered_cmd = cmd
        return func

    return wrapper


@cmd_handler_cls
class Client(BaseClient):

    def handle(self, msg):
        try:
            msg_handler_func = getattr(self, self.handlers[msg.cmd])
        except KeyError:
            raise NoHandlerForCmdRegisteredException(msg.cmd)
        return msg_handler_func(msg)

    @register_cmd(CMD_LOGIN)
    def login_as(self, msg):
        """
        Login client
        """
        if len(msg.params) != 2:
            raise InvalidUserCredentials()
        else:
            name, password = msg.params
        if self.user:
            raise ClientIsAlreadyLoggedInException(self.user)
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
        log.info(ONLINE_USERS)

    @register_cmd(CMD_LOGOUT)
    @login_required
    def logout(self, msg=None):
        """
        Logout client
        """
        log.info("{user} logged out from {client}".format(user=self.user, client=self))
        self.user = None
        log.info(ONLINE_USERS)

    @register_cmd(CMD_FRIENDS)
    @login_required
    def get_friends(self, msg):
        """
        Returns dict {friend's name: info}
        """
        online_only = False  # TODO: to message params
        res = {}
        for friend in self.user.all_friends:
            if friend.name in ONLINE_USERS:
                res[friend.name] = ONLINE_USERS[friend.name].status
            elif not online_only:
                res[friend.name] = CLIENT_OFFLINE
        self.send(PayloadMessage(CMD_INFO, [], res))

    @register_cmd(CMD_MESSAGE)
    @login_required
    def send_message_to(self, msg):
        # verify msg
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

import logging
from functools import wraps

from server.models.utils import get_user_by_name
from server.models.user import User
from server.models.utils import update_user_last_online_ts, create_message, get_messages

from server.online import ONLINE_USERS

from server.base_client import BaseClient, CLIENT_OFFLINE, ClientIsAlreadyLoggedInException

from server.messages import CMD_INFO, CMD_LOGIN, CMD_LOGOUT, CMD_FRIENDS, CMD_MESSAGE
from server.messages import PayloadMessage


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
        log.info("Handle message %s from %s" % (msg, self))
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
        user = get_user_by_name(name)
        if user:
            if user.name in ONLINE_USERS:
                raise UserAlreadyLoggedInException(user.name)
            else:
                if user.password == password:
                    log.info("{user} was logged in from {client}".format(user=user, client=self))
                else:
                    raise InvalidUserCredentials()
                self.user = user
                messages = get_messages(self.user, from_ts=self.user.last_online_ts)
                for m in messages:
                    self.send(PayloadMessage(CMD_MESSAGE, [m.by.name], m.data))
                update_user_last_online_ts(self.user)
        else:
            raise InvalidUserCredentials()

    @register_cmd(CMD_LOGOUT)
    @login_required
    def logout(self, msg=None):
        """
        Logout client
        """
        update_user_last_online_ts(self.user)
        log.info("{user} logged out from {client}".format(user=self.user, client=self))
        self.user = None

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
        user_to = get_user_by_name(to)
        if not user_to:
            raise NoSuchUserException(to)
        if user_to.name not in [u.name for u in self.user.all_friends]:
            raise NoSuchFriendException(to)

        # save msg to db
        create_message(user_to, self.user, msg.payload)

        if user_to.name in ONLINE_USERS:
            ONLINE_USERS[to].send(PayloadMessage(msg.cmd, [self.user.name], msg.payload))

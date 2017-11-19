import logging
from functools import wraps

from server.models import session
from server.models.user import User
from server.models.chat import Chat
from server.models.utils import create_chat, get_chat_by_id, add_chat_participant
from server.online import ONLINE_USERS
from server.config import LoadTestConfig

from server.base_client import BaseClient, CLIENT_OFFLINE, ClientIsAlreadyLoggedInException

from protocol.messages import CMD_INFO, CMD_LOGIN, CMD_LOGOUT, CMD_FRIENDS, CMD_MESSAGE, CMD_CHAT_MESSAGE, \
    CMD_GET_CHATS, CMD_ADD_CHAT_PARTICIPANT, CMD_CREATE_CHAT
from protocol.messages import PayloadMessage

from server.models.utils import update_user_last_online_ts, create_message, get_messages, get_user_by_name


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


class InvalidChatID(Exception):
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
        log.info("{user} logged out from {client}".format(user=self.user, client=self))
        update_user_last_online_ts(self.user)
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
        if (user_to.name not in [u.name for u in self.user.all_friends] and
           not isinstance(self.server.config, LoadTestConfig)):
            raise NoSuchFriendException(to)

        # save msg to db
        create_message(user_to, self.user, msg.payload)

        if user_to.name in ONLINE_USERS:
            ONLINE_USERS[to].send(PayloadMessage(msg.cmd, [self.user.name], msg.payload))

    @register_cmd(CMD_CREATE_CHAT)
    @login_required
    def create_chat(self, msg):
        """
        Create new chat and send new chat id back to the client
        """
        chat_name = msg.params[0]
        new_chat = create_chat(chat_name, self.user)

        log.info("New chat '{}' has been created".format(new_chat))
        self.send(PayloadMessage(CMD_INFO, [], str(new_chat.id)))

    @register_cmd(CMD_ADD_CHAT_PARTICIPANT)
    @login_required
    def add_chat_participant(self, msg):
        """
        Add new participants to the chat
        """
        chat_id = msg.params[0]
        participant_name = msg.params[1]
        chat = get_chat_by_id(chat_id)
        if not chat:
            raise InvalidChatID(chat)
        if self.user.name not in [user.name for user in chat.users]:
            raise InvalidChatID

        add_chat_participant(chat_id, participant_name)

    @register_cmd(CMD_GET_CHATS)
    @login_required
    def get_chats(self, msg):
        """
        get all available chats for user
        """
        self.send(PayloadMessage(CMD_INFO, [], self.user.chats))

    @register_cmd(CMD_CHAT_MESSAGE)
    @login_required
    def sent_message_to_chat(self, msg):
        """
        Send message to all online users in chat
        """
        log.info('User {user} sent message {msg} to chat'.format(user=self.user, msg=msg))
        chat_id = msg.params[0]
        # verify to
        chat = get_chat_by_id(chat_id)
        if not chat:
            raise InvalidChatID(chat)
        users_to = [user.name for user in chat.users]
        log.debug('Found users {users_to} for chat with id {chat_id}'.format(users_to=users_to, chat_id=chat_id))

        if not users_to or self.user.name not in users_to:
            raise InvalidChatID(chat_id)

        for user_to in users_to:
            if user_to == self.user.name:
                continue
            if user_to in ONLINE_USERS:
                # send msg
                log.info('Send MSG {msg} for chat with id {chat_id} to {usr}'.format(
                    msg=msg.payload, chat_id=chat_id, usr=users_to))
                ONLINE_USERS[user_to].send(PayloadMessage(msg.cmd, [chat_id, self.user.name], msg.payload))
            else:
                log.debug("User {} isn't online".format(user_to))

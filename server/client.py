import logging
from functools import wraps

from server.models import session
from server.models.user import User
from server.models.chat import Chat
from server.online import ONLINE_USERS

from server.base_client import BaseClient, CLIENT_OFFLINE, ClientIsAlreadyLoggedInException

from server.messages import CMD_INFO, CMD_LOGIN, CMD_LOGOUT, CMD_FRIENDS, CMD_MESSAGE, CMD_CHAT_MESSAGE, \
    CMD_GET_CHATS, CMD_ADD_CHAT_PARTICIPANT, CMD_CREATE_CHAT
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

    @register_cmd(CMD_LOGOUT)
    @login_required
    def logout(self, msg=None):
        """
        Logout client
        """
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
        user_to = session().query(User).filter(User.name == to).one()
        if not user_to:
            raise NoSuchUserException(to)
        if user_to.name not in [u.name for u in self.user.all_friends]:
            raise NoSuchFriendException(to)
        if user_to.name not in ONLINE_USERS:
            raise NoSuchUserOnlineException(to)

        # send msg
        ONLINE_USERS[to].send(PayloadMessage(msg.cmd, [self.user.name], msg.payload))


    @register_cmd(CMD_CREATE_CHAT)
    @login_required
    def create_chat(self, msg):
        """
        :return: none
        """
        chat_name = msg.payload
        chat = Chat(chat_name, owner=self.user, users=[self.user,])
        db_session = session().object_session(chat)
        db_session.add(chat)
        db_session.commit()
        log.info("New chat '{}' has been created".format(chat))
        self.send(PayloadMessage(CMD_INFO, [], str(chat.id)))

    @register_cmd(CMD_ADD_CHAT_PARTICIPANT)
    @login_required
    def add_chat_participant(self, msg):
        """
        :return: None
        """
        chat_id = msg.params[0]
        participant_name = msg.params[1]
        chat = session().query(Chat).filter(Chat.id == chat_id).first()
        db_session = session().object_session(chat)
        if not chat:
            raise InvalidChatID(chat)
        if self.user.name not in [user.name for user in chat.users]:
            raise InvalidChatID

        chat = db_session.query(Chat).filter(Chat.id == chat_id).one()
        chat.users.append(db_session.query(User).filter(User.name == participant_name).first())
        db_session.add(chat)
        db_session.commit()

    @register_cmd(CMD_GET_CHATS)
    @login_required
    def get_chats(self, msg):
        """
        get all available chats for user
        :return: None
        """
        self.send(PayloadMessage(CMD_INFO, [], self.user.chats))

    @register_cmd(CMD_CHAT_MESSAGE)
    @login_required
    def sent_message_to_chat(self, msg):
        """
        :return: None
        """
        log.info('User {user} sent message {msg} to chat'.format(user=self.user, msg=msg))
        chat_id = msg.params[0]
        # verify to
        chat = session().query(Chat).filter(Chat.id == chat_id).first()
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
                ONLINE_USERS[user_to].send(PayloadMessage(msg.cmd, [chat_id, self.user.name], msg.payload))

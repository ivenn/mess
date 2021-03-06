import datetime

from server.models import session
from server.models.user import User
from server.models.chat import Chat
from server.models.message import Message, ChatMessage


s = session()


def create_user(name, password):
    user = get_user_by_name(name)
    if user:
        print("User with name {name} already exists".format(name=name))
    else:
        user = User(name, password)
        s.add(user)
        s.commit()

    return user


def create_users(name_pass=None, num=1):
    """
    @param name_pass: list of tuples like (name, password)
    @param num: number of users to generate if no explicit names/passwords are provided
    """
    users = {}
    name_pass = name_pass if name_pass else [('user%s' % n, 'pass%s' % n) for n in range(num)]

    # create user in they don't exist
    for name, passwd in name_pass:
        users[name] = create_user(name, passwd)

    return users


def make_friends(user, new_friends):
    """
    @param user: User model instance to add friends to
    @param new_friends: List of User models
    """
    user.friends += new_friends
    s.commit()


def get_user_by_name(name):
    res = s.query(User).filter(User.name == name).all()
    if len(res) == 1:
        return res[0]
    elif res:
        raise Exception("More than one user with name {name} was found".format(name=name))
    else:
        return None


def update_user_last_online_ts(user):
    user.last_online_ts = datetime.datetime.utcnow()
    s.commit()


def create_message(to_user, from_user, data):
    message = Message(data, by=from_user, to=to_user)
    s.add(message)
    s.commit()


def get_messages(to_user, by_user=None, from_ts=None, to_ts=None):
    if not from_ts:
        from_ts = 0
    if not to_ts:
        to_ts = datetime.datetime.utcnow()
    if to_user and by_user:
        return s.query(Message).filter(
            Message.to_id == to_user.id).filter(
            Message.by_id == by_user.id).filter(
            Message.created_ts.between(from_ts, to_ts)).all()
    else:
        return s.query(Message).filter(
            Message.to_id == to_user.id).filter(
            Message.created_ts.between(from_ts, to_ts)).all()


def create_chat_message(to_chat, from_user, data):
    message = ChatMessage(data, chat=to_chat, by=from_user)
    s.add(message)
    s.commit()


def get_chat_messages(chat_id, from_ts=None, to_ts=None):
    if not from_ts:
        from_ts = 0
    if not to_ts:
        to_ts = datetime.datetime.utcnow()
    return s.query(ChatMessage).filter(
        ChatMessage.chat_id == chat_id).filter(
        ChatMessage.created_ts.between(from_ts, to_ts)).all()


def create_chat(name, chat_owner, participants=None):
    """
    Create chat
    :param name: name of new chat
    :param chat_owner: User instance of chat owner
    :param participants: List of Users instants
    :return: chat object
    """
    participants = participants if participants else []
    chat = Chat(name, chat_owner)
    participants.append(chat_owner)
    chat.users = participants
    s.add(chat)
    s.commit()
    return chat


def get_chat_by_id(chat_id):
    """
    Find out Chat in DB by chat id
    :param chat_id: chat id
    :return: Chat object if or None if there is no chat this such ID
    """
    return s.query(Chat).filter(Chat.id == chat_id).first()


def add_chat_participant(chat_id, participant_name):
    """
    Add chat participant to existent chat
    :param chat_id: Chat object
    :param participant_name: User name
    :return: None
    """
    chat = get_chat_by_id(chat_id)
    chat.users.append(s.query(User).filter(User.name == participant_name).first())
    s.add(chat)
    s.commit()


def create_chat(name, chat_owner, participants=None):
    """
    Create chat
    :param name: name of new chat
    :param chat_owner: User instance of chat owner
    :param participants: List of Users instants
    :return: chat object
    """
    participants = participants if participants else []
    chat = Chat(name, chat_owner)
    participants.append(chat_owner)
    chat.users = participants
    s.add(chat)
    s.commit()
    return chat


def get_chat_by_id(chat_id):
    """
    Find out Chat in DB by chat id
    :param chat_id: chat id
    :return: Chat object if or None if there is no chat this such ID
    """
    return s.query(Chat).filter(Chat.id == chat_id).first()


def add_chat_participant(chat_id, participant_name):
    """
    Add chat participant to existent chat
    :param chat_id: Chat object
    :param participant_name: User name
    :return: None
    """
    chat = get_chat_by_id(chat_id)
    chat.users.append(s.query(User).filter(User.name == participant_name).first())
    s.add(chat)
    s.commit()

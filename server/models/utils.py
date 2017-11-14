import datetime

from server.models import session
from server.models.user import User
from server.models.chat import Chat
from server.models.message import Message


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

from functools import wraps


class UserAlreadyLoggedInException(Exception):
    pass


class UserIsNotLoggedInException(Exception):
    pass


class NoSuchUserException(Exception):
    pass


class NoSuchChatException(Exception):
    pass


def login_required(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        user = args[0]
        if not user.logged_in:
            raise UserIsNotLoggedInException(user.name)
        return func(*args, **kwargs)

    return wrapped


class User:

    def __init__(self, conn, name):
        self.name = name
        self.conn = conn
        self.logged_in = False
        self.chats = {}  # {username: <User> instance}

    def __repr__(self):
        return "%s: %s" % (self.name, self.conn)

    def login(self):
        self.logged_in = True
        print("User @%s is logged in" % self.name)

    def logout(self):
        for name in self.chats:
            self.send_to(name, "User @%s exited from chat" % self.name)
        self.logged_in = False
        print("@%s is logged out" % self.name)

    @login_required
    def invite(self, user):
        if not user.logged_in:
            raise UserIsNotLoggedInException(user.name)
        else:
            self.chats[user.name] = user
            user.chats[self.name] = self
            self.send_to(user, "@%s invited you to chat" % self.name)
            print("@%s invited @%s" % (self.name, user.name))

    @login_required
    def leave_chat(self, user):
        if not user.logged_in:
            raise UserIsNotLoggedInException(user.name)
        if user.name not in self.chats:
            raise NoSuchChatException("@%s + @%s" % (self.name, user.name))
        else:
            self.send_to(user, "@%s leaving chat" % self.name)
            del user.chats[self.name]
            self.send("Leaving chat with %s" % user.name)
            del self.chats[user.name]
            print("@%s leaves chat with @%s" % (self.name, user.name))

    @login_required
    def send(self, msg):
        bmsg = msg.encode('utf-8')
        self.conn.send(bmsg + b'\n')
        print("@%s get message '%s'" % (self.name, msg))

    @login_required
    def send_to(self, user, msg):
        if user.name not in self.chats:
            raise NoSuchChatException("%s + %s" % (self.name, user.name))
        else:
            msg = "[%s]: %s" % (self.name, msg)
            user.send(msg)
            print("@%s sent '%s' to @%s" % (self.name, msg, user.name))

    @login_required
    def status(self):
        print("@%s requested status info" % self.name)
        return self.send("LOGIN_AS: %s, CHATS: %s" % (self.name, ','.join(self.chats.keys())))
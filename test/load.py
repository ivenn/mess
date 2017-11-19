from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import traceback
import random
from queue import Queue, Empty
from collections import defaultdict
import time
from test.lib.user import TestUser


USERS_NUM = 3

REGISTER = {}


class LoadTestUserWrapper:

    def __init__(self, user):
        self.user = user
        self.stat = defaultdict(int)
        self.mailbox = Queue()
        REGISTER[self.user.name] = self.mailbox

    def __repr__(self):
        return str(self.user)

    @property
    def name(self):
        return self.user.name

    def connect(self):
        self.user.connect()
        self.stat['connect'] += 1

    def disconnect(self):
        self.user.disconnect()
        self.stat['disconnect'] += 1

    def login(self):
        self.user.login()
        self.stat['login'] += 1

    def logout(self):
        self.user.logout()
        self.stat['logout'] += 1

    def get_friends(self):
        self.user.get_friends()
        self.stat['get_friends'] += 1

    def send_msg(self, msg):
        user_list_to_choose = list(REGISTER.keys())
        user_list_to_choose.remove(self.user.name)
        send_to = random.choice(user_list_to_choose)
        print('%s sending message to %s' % (self.name, send_to))
        self.user.send(msg, send_to)
        REGISTER[send_to].put(msg, timeout=1)
        self.stat['send_msg'] += 1

    def wait_msg(self, timeout=5):
        msgs = self.user.recv_msg(timeout=timeout)
        print(msgs)
        if msgs is list:
            for _ in msgs[1:]:
                self.mailbox.get(timeout=1)
        self.stat['wait_msg'] += 1


def test(test_user):
    user = LoadTestUserWrapper(test_user)
    for _ in range(1):
        try:
            user.connect()
            time.sleep(0.1)
            for _ in range(2):
                user.login()
                time.sleep(1)
                for _ in range(10):
                    try:
                        user.mailbox.get(timeout=1)
                        user.wait_msg()
                    except Empty:
                        user.send_msg('msg')
                    time.sleep(1)
                user.logout()
            time.sleep(0.1)
            user.disconnect()
        except Exception as e:
            print(user)
            print('%s: %s' % (user.name, traceback.print_exc()))
    return user.stat


def main():
    exe = ThreadPoolExecutor(USERS_NUM)
    up = [('user%s' % i, 'pass%s' % i) for i in range(USERS_NUM)]

    future_to_test = {user: exe.submit(test, TestUser(user, password)) for user, password in up}
    time.sleep(30)

    for uname, res in future_to_test.items():
        try:
            r = res.result(10)
            print("%s: %s" % (uname, r))
        except Exception as e:
            print(e)
    print(future_to_test)


if __name__ == '__main__':
    main()
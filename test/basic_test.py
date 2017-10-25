import unittest
import time

from test.lib.user import TestUser
from test.lib.test_server import TestServer

from server.models import init_db
from server.models.utils import create_users, make_friends
from server.base_client import USER_STATUS_DEFAULT, CLIENT_OFFLINE
from server.config import PROJECT_PATH

from protocol.messages import NormalMessage, CMD_CHANGE_STATUS


class TestFunctional(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = TestServer()
        init_db(db=cls.server.config.db, enable_logging=False)
        cls.name_pass1 = ('user1', 'pass1')
        cls.name_pass2 = ('user2', 'pass2')
        cls.name_pass3 = ('user3', 'pass3')
        cls.users = create_users(name_pass=[cls.name_pass1, cls.name_pass2, cls.name_pass3, ])
        make_friends(cls.users[cls.name_pass1[0]], [cls.users[cls.name_pass2[0]], cls.users[cls.name_pass3[0]]])

    def setUp(self):
        self.server.up()

    def tearDown(self):
        self.server.down()
        self.server.kill()

    def test_connect_disconnect(self):
        print("== Connect/disconnect")
        self.user1 = TestUser(self.name_pass1[0], self.name_pass1[1])
        self.user1.connect()
        self.user1.disconnect()

    def test_login_logout(self):
        print("== Login/logout scenario")
        self.user1 = TestUser(self.name_pass1[0], self.name_pass1[1])
        self.user1.connect()
        self.user1.login()
        self.user1.logout()
        self.user1.disconnect()

    def test_friend_status_change(self):
        print("== State change notifications to friends")

        self.user1 = TestUser(self.name_pass1[0], self.name_pass1[1])
        self.user2 = TestUser(self.name_pass2[0], self.name_pass2[1])

        self.user1.connect()
        self.user2.connect()

        self.user1.login()

        self.user2.login()
        msg1 = self.user1.recv_msg(timeout=1)
        self.assertEqual(NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user2.name, USER_STATUS_DEFAULT]),
                         msg1)

        self.user2.logout()
        msg2 = self.user1.recv_msg(timeout=1)
        self.assertEqual(NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user2.name, CLIENT_OFFLINE]),
                         msg2)

        self.user1.logout()

        self.user1.disconnect()
        self.user2.disconnect()

    def test_x(self):
        print("test_x")
        self.user1 = TestUser(self.name_pass1[0], self.name_pass1[1])
        self.user2 = TestUser(self.name_pass2[0], self.name_pass2[1])
        self.user3 = TestUser(self.name_pass3[0], self.name_pass3[1])

        self.user1.connect()
        self.user2.connect()
        self.user3.connect()

        self.user1.login()
        time.sleep(0.1)
        self.user2.login()
        time.sleep(0.1)
        self.user3.login()
        time.sleep(0.1)

        self.user1.disconnect()
        self.user2.disconnect()
        self.user3.disconnect()


if __name__ == '__main__':
    unittest.main()

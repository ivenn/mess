import unittest

from test.lib.test_user import TestUser
from test.lib.test_server import TestServer

from server.messages import NormalMessage, CMD_CHANGE_STATUS
from server.models import init_db
from server.models.utils import create_users, make_friends


class TestFunctional(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = TestServer(stdout=False)
        init_db(db=cls.server.config.db, enable_logging=False)
        cls.user1 = ('user1', 'pass1')
        cls.user2 = ('user2', 'pass2')
        cls.users = create_users(name_pass=[cls.user1, cls.user2, ])
        make_friends(cls.users[cls.user1[0]], [cls.users[cls.user2[0]], ])

    def setUp(self):
        self.server.up()

        self.test_user1 = TestUser(self.user1[0], self.user1[1])
        self.test_user2 = TestUser(self.user2[0], self.user2[1])
        self.test_user1.connect()
        self.test_user2.connect()

    def test_login_logout(self):
        self.test_user1.login()
        self.test_user2.logout()

    def test_friend_status_change(self):
        self.test_user1.login()
        self.test_user2.login()
        message1 = self.test_user1.recv_msg(timeout=1)

        self.assertEqual(message1,
                         NormalMessage(cmd=CMD_CHANGE_STATUS,
                                       params=['user2', 'ONLINE']))

        self.test_user1.logout()
        message2 = self.test_user2.recv_msg(1)
        self.assertEqual(message2,
                         NormalMessage(cmd=CMD_CHANGE_STATUS,
                                       params=['user1', 'OFFLINE']))

        self.test_user2.logout()

    def tearDown(self):
        self.test_user1.disconnect()
        self.test_user2.disconnect()
        self.server.down()


if __name__ == '__main__':
    unittest.main()

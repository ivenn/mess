import os
import time
import unittest

from test.lib.test_server import TestServer
from test.lib.user import TestUser, NotConnectedException

from server.models import init_db
from server.models.utils import create_users, make_friends


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

    @classmethod
    def tearDownClass(cls):
        print("Deleting sqlite db file...")
        try:
            os.remove(cls.server.config.db_path)
        except OSError:
            pass

    def setUp(self):
        self.user1 = TestUser(self.name_pass1[0], self.name_pass1[1])
        self.user2 = TestUser(self.name_pass2[0], self.name_pass2[1])
        self.user3 = TestUser(self.name_pass3[0], self.name_pass3[1])
        self.users = [self.user1, self.user2, self.user3]
        self.server.up()

    def tearDown(self):
        time.sleep(1)
        for user in self.users:
            try:
                user.disconnect()
            except NotConnectedException:
                pass
        self.server.down()
        if self.server.pid:
            self.server.kill()

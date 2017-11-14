import unittest
import time

from server.base_client import USER_STATUS_DEFAULT, CLIENT_OFFLINE
from protocol.messages import NormalMessage, CMD_CHANGE_STATUS

from test.base_test import TestFunctional


class TestFunctionalBasic(TestFunctional):

    def test_connect_disconnect(self):
        print("== Connect/disconnect")
        self.user1.connect()
        self.user1.disconnect()

    def test_login_logout(self):
        print("== Login/logout scenario")
        self.user1.connect()
        self.user1.login()
        self.user1.logout()
        self.user1.disconnect()

    def test_friend_status_change(self):
        print("== State change notifications to friends")
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

    def test_race_broken_pipe(self):
        print("test_race_broken_pipe")
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

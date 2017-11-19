import unittest

from test.base_test import TestFunctional
from server.base_client import USER_STATUS_DEFAULT, CLIENT_OFFLINE

from protocol.messages import NormalMessage, PayloadMessage, CMD_CHANGE_STATUS, CMD_MESSAGE


class TestFunctionalOfflineMessages(TestFunctional):

    SIMPLE_MESSAGE_STR = "ping"
    ANOTHER_ONE_MESSAGE_STR = "pong"

    def test_simple_message(self):
        print("== Simple personal messaging scenario")

        self.user1.connect()
        self.user2.connect()

        self.user1.login()

        self.user2.login()
        msg1 = self.user1.recv_msg(timeout=1)
        self.assertEqual(
            NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user2.name, USER_STATUS_DEFAULT]),
            msg1)

        self.user1.send(msg=self.SIMPLE_MESSAGE_STR, to=self.user2.name)
        msg2 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            PayloadMessage(cmd=CMD_MESSAGE, params=[self.user1.name, ], payload=self.SIMPLE_MESSAGE_STR),
            msg2)

        self.user2.send(msg=self.ANOTHER_ONE_MESSAGE_STR, to=self.user1.name)
        msg3 = self.user1.recv_msg(timeout=1)
        self.assertEqual(
            PayloadMessage(cmd=CMD_MESSAGE, params=[self.user2.name, ], payload=self.ANOTHER_ONE_MESSAGE_STR),
            msg3)

        self.user1.logout()
        msg4 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user1.name, CLIENT_OFFLINE]),
            msg4)

        self.user2.logout()
        self.user1.disconnect()
        self.user2.disconnect()

    def test_get_saved_messages(self):
        print("== User get saved personal messages after login")
        self.user1.connect()
        self.user2.connect()

        self.user1.login()

        self.user1.send(msg=self.SIMPLE_MESSAGE_STR, to=self.user2.name)
        self.user1.send(msg=self.ANOTHER_ONE_MESSAGE_STR, to=self.user2.name)

        self.user2.login()
        msg1 = self.user1.recv_msg(timeout=1)
        self.assertEqual(
            NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user2.name, USER_STATUS_DEFAULT]),
            msg1)

        msg2 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            PayloadMessage(cmd=CMD_MESSAGE, params=[self.user1.name, ], payload=self.SIMPLE_MESSAGE_STR),
            msg2)
        msg3 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            PayloadMessage(cmd=CMD_MESSAGE, params=[self.user1.name, ], payload=self.ANOTHER_ONE_MESSAGE_STR),
            msg3)

        self.user1.logout()
        msg4 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user1.name, CLIENT_OFFLINE]),
            msg4)

        self.user2.send(msg=self.SIMPLE_MESSAGE_STR, to=self.user1.name)
        self.user2.send(msg=self.ANOTHER_ONE_MESSAGE_STR, to=self.user1.name)

        self.user1.login()
        msg5 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user2.name, USER_STATUS_DEFAULT]),
            msg5)

        msg6 = self.user1.recv_msg(timeout=1)
        self.assertEqual(
            PayloadMessage(cmd=CMD_MESSAGE, params=[self.user2.name, ], payload=self.SIMPLE_MESSAGE_STR),
            msg6)
        msg7 = self.user1.recv_msg(timeout=1)
        self.assertEqual(
            PayloadMessage(cmd=CMD_MESSAGE, params=[self.user2.name, ], payload=self.ANOTHER_ONE_MESSAGE_STR),
            msg7)

        self.user1.logout()
        msg8 = self.user2.recv_msg(timeout=1)
        self.assertEqual(
            NormalMessage(cmd=CMD_CHANGE_STATUS, params=[self.user1.name, CLIENT_OFFLINE]),
            msg8)

        self.user2.logout()
        self.user1.disconnect()
        self.user2.disconnect()


if __name__ == '__main__':
    unittest.main()

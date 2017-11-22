import unittest
import time
import re
import os

from test.lib.user import TestUser
from test.lib.test_server import TestServer

from server.models import init_db
from server.models.utils import create_users, create_chat

from protocol.messages import CMD_CHAT_MESSAGE, CMD_GET_CHATS, CMD_CREATE_CHAT

from logging import getLogger


log = getLogger("chat_test")


class TestFunctional(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        print("Deleting sqlite db file...")
        try:
            os.remove(cls.server.config.db_path)
        except OSError:
            pass

    @classmethod
    def setUpClass(cls):
        cls.server = TestServer()
        init_db(db=cls.server.config.db, enable_logging=False)
        cls.name_pass1 = ('user1', 'pass1')
        cls.name_pass2 = ('user2', 'pass2')
        cls.name_pass3 = ('user3', 'pass3')
        cls.name_pass4 = ('user4', 'pass4')
        cls.users = create_users(name_pass=[cls.name_pass1, cls.name_pass2, cls.name_pass3, cls.name_pass4])

        cls.base_chat_name = 'Prepared_chat'
        cls.base_chat = create_chat(
            cls.base_chat_name, cls.users[cls.name_pass4[0]],
            [cls.users[cls.name_pass3[0]], cls.users[cls.name_pass2[0]], cls.users[cls.name_pass1[0]]])

    def setUp(self):
        self.server.up()

    def tearDown(self):
        time.sleep(1)
        self.server.down()
        if self.server.pid:
            self.server.kill()

    @staticmethod
    def getLoggedInUser(login_password):
        user = TestUser(login_password[0], login_password[1])
        user.connect()
        user.login()
        return user

    @staticmethod
    def disconnect_users(users):
        for user in users:
            user.logout()
            user.disconnect()

    def _test_send_chat_message(self):
        print("== Test send chat message test")
        self.user4 = self.getLoggedInUser(self.name_pass4)
        self.user3 = self.getLoggedInUser(self.name_pass3)
        self.user1 = self.getLoggedInUser(self.name_pass1)
        time.sleep(2)

        print("Send message")
        msg_text = "First message"
        self.user4.send_message(
            "{cmd} {chat_id} {payload_size}||{msg}..".format(cmd=CMD_CHAT_MESSAGE,
                                                             chat_id=self.base_chat.id,
                                                             payload_size=len(msg_text),
                                                             msg=msg_text))

        msg_usr1 = self.user1.recv_msg()
        msg_usr3 = self.user3.recv_msg()
        self.assertEqual(msg_usr1.payload, msg_usr3.payload, "All users should receive the same message")
        self.assertEqual(msg_usr1.payload, msg_text, "Users should receive the right message")

        self.disconnect_users([self.user4, self.user3, self.user1])

    def test_chat_offline_message(self):
        print("== Test offline chat messages")
        firs_offline_message = "first offline message"
        second_offline_message = "second offline message"
        self.user4 = self.getLoggedInUser(self.name_pass4)
        time.sleep(2)
        print("Send first message")

        self.user4.send_message(
            "{cmd} {chat_id} {payload_size}||{msg}..".format(cmd=CMD_CHAT_MESSAGE,
                                                             chat_id=self.base_chat.id,
                                                             payload_size=len(firs_offline_message),
                                                             msg=firs_offline_message))
        print("Login new user and check message")
        self.user3 = self.getLoggedInUser(self.name_pass3)
        first_msg_usr3 = self.user3.recv_msg()
        self.assertEqual(firs_offline_message, first_msg_usr3.payload, "User should receive offline message")

        self.user4.send_message(
            "{cmd} {chat_id} {payload_size}||{msg}..".format(cmd=CMD_CHAT_MESSAGE,
                                                             chat_id=self.base_chat.id,
                                                             payload_size=len(second_offline_message),
                                                             msg=second_offline_message))

        second_msg_usr3 = self.user3.recv_msg()
        self.assertEqual(second_offline_message, second_msg_usr3.payload, "User online and should receive new message")

        self.user1 = self.getLoggedInUser(self.name_pass1)
        first_msg_usr1 = self.user1.recv_msg()
        second_msg_usr1 = self.user1.recv_msg()
        self.assertEqual(firs_offline_message, first_msg_usr1.payload,
                         "User logged in and should receive all offline messages")
        self.assertEqual(second_offline_message, second_msg_usr1.payload, "User should receive offline message")

        self.disconnect_users([self.user4, self.user3, self.user1])

    def _test_create_new_chat(self):
        print("== Create new chat test")
        self.user2 = self.getLoggedInUser(self.name_pass2)
        time.sleep(2)
        new_chat_name = "New chat name"
        self.user2.send_message("{cmd} {chat_name}..".format(
            cmd=CMD_CREATE_CHAT, chat_name=new_chat_name))
        msg_with_chat_id = self.user2.recv_msg()
        new_chat_id = msg_with_chat_id.payload
        self.user2.send_message("{cmd}..".format(cmd=CMD_GET_CHATS))
        msg_usr2 = self.user2.recv_msg()

        # TODO: fix while introducing new InfoMessage
        """
        self.assertTrue(
            re.search("Chat\(id={id}, name={chat_name}, owner=User\({user_name}\)".format(id=new_chat_id,
                                                                                          chat_name=new_chat_name,
                                                                                          user_name=self.name_pass2[0]),
                      msg_usr2.payload))
        """
        self.disconnect_users([self.user2])


if __name__ == '__main__':
    unittest.main()

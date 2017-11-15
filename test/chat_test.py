import unittest
import time
import re

from test.lib.user import TestUser
from test.lib.test_server import TestServer

from server.models import init_db
from server.models.utils import create_users, create_chat

from protocol.messages import CMD_CHAT_MESSAGE, CMD_GET_CHATS, CMD_CREATE_CHAT

from logging import getLogger
log = getLogger("chat_test")


class TestFunctional(unittest.TestCase):

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
        self.server.down()
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

    def test_send_chat_message(self):
        print("== Test send chat message test")
        self.user4 = self.getLoggedInUser(self.name_pass4)
        self.user3 = self.getLoggedInUser(self.name_pass3)
        self.user1 = self.getLoggedInUser(self.name_pass1)
        time.sleep(2)

        print("Send message")
        msg_text = "First message"
        self.user4.send_message(
            "{cmd} {chat_id} ||{msg}..".format(cmd=CMD_CHAT_MESSAGE, chat_id=self.base_chat.id, msg=msg_text))

        msg_usr1 = self.user1.recv_msg()
        msg_usr3 = self.user3.recv_msg()
        self.assertEqual(msg_usr1.payload, msg_usr3.payload, "All users should receive the same message")
        self.assertEqual(msg_usr1.payload, msg_text, "Users should receive the right message")

        self.disconnect_users([self.user4, self.user3, self.user1])

    def test_create_new_chat(self):
        print("== Create new chat test")
        self.user2 = self.getLoggedInUser(self.name_pass2)
        time.sleep(2)
        new_chat_name = "New chat name"
        self.user2.send_message(
            "{cmd} ||{msg}..".format(cmd=CMD_CREATE_CHAT, chat_id=self.base_chat.id, msg=new_chat_name))
        msg_with_chat_id = self.user2.recv_msg()
        new_chat_id = msg_with_chat_id.payload
        self.user2.send_message("{cmd}..".format(cmd=CMD_GET_CHATS))
        msg_usr2 = self.user2.recv_msg()
        self.assertTrue(
            re.search("Chat\(id={id}, name={chat_name}, owner=User\({user_name}\)".format(id=new_chat_id,
                                                                                          chat_name=new_chat_name,
                                                                                           user_name=self.name_pass2[0]),
                      msg_usr2.payload))

        self.disconnect_users([self.user2])


if __name__ == '__main__':
    unittest.main()

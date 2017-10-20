import unittest

from server.models import session, init_db
from server.models.user import User
from server.models.chat import Chat


class TestChatModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db('sqlite:///:memory:')

    def setUp(self):
        self.db_session = session()

    def test_basic(self):
        name1, pass1 = ('user1', 'pass1')
        name2, pass2 = ('user2', 'pass2')
        chat_name = 'test_chat'

        user1 = User(name1, pass1)
        user2 = User(name2, pass2)

        for u in [user1, user2]:
            self.db_session.add(u)

        self.db_session.commit()

        new_chat = Chat(chat_name, user1, [user1, user2])
        self.db_session.add(new_chat)
        self.db_session.commit()

        # check that chat exists
        chat_from_db = self.db_session.query(Chat).filter(Chat.name == chat_name).one()
        self.assertEqual(chat_from_db, new_chat)

        # check that user1 and user2 has such chat
        self.assertListEqual(user1.chats, [new_chat])
        self.assertListEqual(user2.chats, [new_chat])

    def test_same_user_in_chat_ignored(self):
        name, passwd = ('user3', 'pass3')
        chat_name = 'test_chat2'

        user = User(name, passwd)
        chat = Chat(chat_name, user, [user, ])

        self.db_session.add(user)
        self.db_session.add(chat)

        self.db_session.commit()

        # check created chat
        chat_from_db = self.db_session.query(Chat).filter(Chat.name == chat_name).one()
        self.assertListEqual(chat_from_db.users, [user])

        # try to add same user to the same chat
        chat.users.append(user)
        self.db_session.add(chat)
        self.db_session.commit()

        # check that user was not added twice
        self.assertListEqual(chat_from_db.users, [user])


if __name__ == '__main__':
    unittest.main()

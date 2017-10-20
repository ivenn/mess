import unittest

from server.models import session, init_db
from server.models.user import User
from server.models.message import Message


class TestMessageModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db('sqlite:///:memory:')

    def setUp(self):
        self.db_session = session()

    def test_basic(self):
        name1, pass1 = ('user1', 'pass1')
        name2, pass2 = ('user2', 'pass2')

        user1 = User(name1, pass1)
        user2 = User(name2, pass2)

        for u in [user1, user2]:
            self.db_session.add(u)
            self.db_session.commit()

        # create message
        message = Message('Hello!', by=user1, to=user2)
        self.db_session.add(message)
        self.db_session.commit()

        # check that it appeared in db
        message_from_db = self.db_session.query(Message).filter(
            Message.by == user1).filter(
            Message.to == user2).first()

        # verify recieved message
        self.assertEqual(message_from_db, message)


if __name__ == '__main__':
    unittest.main()

import unittest

from sqlalchemy.exc import IntegrityError

from server.models import session, init_db
from server.models.user import User


class TestUserModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db('sqlite:///:memory:')

    def setUp(self):
        self.db_session = session()

    def test_crud_user(self):
        test_name = 'userT'
        test_password = 'passT'
        test_user = User(test_name, test_password)

        self.db_session.add(test_user)
        self.db_session.commit()

        users = self.db_session.query(User).filter(User.name == test_name).all()
        self.assertEqual(len(users), 1)
        created_user = users[0]
        self.assertEqual(created_user.name, test_user.name)
        self.assertEqual(created_user.password, test_user.password)

        # update user with new password
        created_user.password = 'new_passT'
        self.db_session.add(created_user)
        self.db_session.commit()
        updated_user = self.db_session.query(User).filter(User.name == test_name).first()
        self.assertEqual(created_user.name, updated_user.name)
        self.assertEqual(created_user.password, updated_user.password)

        # delete user
        self.db_session.delete(test_user)
        self.db_session.commit()
        users = self.db_session.query(User).filter(User.name == test_name).all()
        self.assertListEqual(users, [])

    def test_friendship(self):
        name1, pass1 = ('user1', 'pass1')
        name2, pass2 = ('user2', 'pass2')

        user1 = User(name1, pass1)
        user2 = User(name2, pass2)

        for u in [user1, user2]:
            self.db_session.add(u)
            self.db_session.commit()

        for u in [user1, user2]:
            self.assertListEqual(u.friends, [])
            self.assertListEqual(u.all_friends, [])

        user1.friends.append(user2)
        self.db_session.commit()

        self.assertListEqual(user1.friends, [user2, ])
        self.assertListEqual(user2.friends, [])

        self.assertListEqual(user1.all_friends, [user2, ])
        self.assertListEqual(user2.all_friends, [user1, ])

    def test_self_friendship_fail(self):
        test_name = 'user3'
        test_password = 'pass3'
        test_user = User(test_name, test_password)

        self.db_session.add(test_user)
        self.db_session.commit()

        test_user.friends.append(test_user)
        with self.assertRaises(IntegrityError):
            self.db_session.commit()


if __name__ == '__main__':
    unittest.main()

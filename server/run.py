from server.mess_server import MessServer
from server.models import session, init_db
from server.models.user import User
from server.config import configure_logging


def add_users(db_session):
    for name, passwd in [('userA', 'passA'),
                         ('userB', 'passB')]:
        if not db_session.query(User).filter(User.name == name).all():
            db_session.add(User(name, passwd))
    db_session.commit()


if __name__ == '__main__':
    configure_logging()
    init_db()
    add_users(session())
    MessServer().run()

from server.models import session, init_db
from server.loop import run_server
from server.models.user import User


if __name__ == '__main__':
    init_db()
    s = session()
    for name, passwd in [('userA', 'passA'),
                         ('userB', 'passB')]:
        if not s.query(User).filter(User.name == name).all():
            s.add(User(name, passwd))
    s.commit()
    run_server()

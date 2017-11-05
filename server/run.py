from server.mess_server import MessServer
from server.models import session, init_db
from server.models.user import User
from server.models.chat import Chat
from server.config import configure_logging


def fill_db(db_session):

    users = {}
    name_pass = [('userA', 'passA'), ('userB', 'passB'), ('userC', 'passC'), ('userZ', 'passZ')]

    # create users in they don't exist
    for name, passwd in name_pass:
        existing_user = db_session.query(User).filter(User.name == name).first()
        if existing_user:
            users[name] = existing_user
        else:
            users[name] = User(name, passwd)
            db_session.add(users[name])
    db_session.commit()

    # update friendship
    # A = [B, C]
    # B = [A, C]
    # C = [B, C]
    # Z = []

    users['userA'].friends = [users['userB'], users['userC']]
    users['userB'].friends.append(users['userC'])

    db_session.commit()

    # create chat with participants
    chat_name = 'First_chat'
    chat_owner = 'userZ'
    first_chat = db_session.query(Chat).filter(Chat.name == chat_name and Chat.owner == users[chat_owner]).first()
    if first_chat:
        pass
    else:
        first_chat = Chat(chat_name, users[chat_owner])
    first_chat.users = [users[chat_owner], users['userC'], users['userB']]
    db_session.add(first_chat)
    db_session.commit()



if __name__ == '__main__':
    configure_logging()
    init_db(enable_logging=False)
    s = session()
    fill_db(s)
    MessServer().run()

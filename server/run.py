from optparse import OptionParser

from server.mess_server import MessServer
from server.models import session, init_db
from server.models.chat import Chat
from server.models.utils import create_users, create_chat
from server.config import Config, TestConfig, LoadTestConfig 
from server.config.log import configure_logging


RUN_MODE_TEST = 'test'
RUN_MODE_LOAD = 'load'


def fill_db_load():
    users_to_create = [('user%s' % i, 'pass%s' % i) for i in range(100)]
    users = create_users(users_to_create)
    s = session()
    s.commit()


def fill_db():
    users = create_users([('userA', 'passA'),
                          ('userB', 'passB'),
                          ('userC', 'passC'),
                          ('userZ', 'passZ')])

    # update friendship to have:
    # A = [B, C]
    # B = [A, C]
    # C = [B, C]
    # Z = []
    s = session()
    users['userA'].friends = [users['userB'], users['userC']]
    users['userB'].friends.append(users['userC'])
    s.commit()

    # create chat with participants
    chat_name = 'First_chat'
    chat_owner = 'userZ'
    first_chat = s.query(Chat).filter(Chat.name == chat_name and Chat.owner == users[chat_owner]).first()
    if not first_chat:
        create_chat(chat_name, users[chat_owner], [users['userC'], users['userB']])


def main(mode=None, create_config=False):
    if mode == RUN_MODE_TEST:
        config = TestConfig()
    elif mode == RUN_MODE_LOAD:
        config = LoadTestConfig()
    else:
        config = Config()

    print("LOG_PATH={log_path}".format(log_path=config.log))
    print("DB_PATH={db_path}".format(db_path=config.db))

    configure_logging(log_path=config.log)
    init_db(db=config.db, enable_logging=False)

    if mode != RUN_MODE_TEST and create_config:
        print("Creating configuration...")
        if RUN_MODE_LOAD:
            fill_db_load()
        else:
            fill_db()

    MessServer(config=config).run()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m",
                      "--mode",
                      dest="mode",
                      help="server run mode")
    parser.add_option("-c",
                      "--config",
                      action="store_true",
                      dest="config",
                      default=False,
                      help="create basic configuration")

    (options, args) = parser.parse_args()

    main(mode=options.mode, create_config=options.config)

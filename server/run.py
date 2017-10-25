from optparse import OptionParser

from server.mess_server import MessServer
from server.models import session, init_db
from server.models.utils import create_users
from server.config import Config, TestConfig
from server.config.log import configure_logging


RUN_MODE_TEST = 'test'


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


def main(mode=None):
    if mode == RUN_MODE_TEST:
        config = TestConfig()
    else:
        config = Config()

    print("LOG_PATH={log_path}".format(log_path=config.log))
    print("DB_PATH={db_path}".format(db_path=config.db))

    configure_logging(log_path=config.log)
    init_db(db=config.db, enable_logging=False)
    #fill_db()

    MessServer().run()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m",
                      "--mode",
                      dest="mode",
                      help="server run mode")
    (options, args) = parser.parse_args()

    main(mode=options.mode)

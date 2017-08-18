import socket
import select
import re
import traceback
from logging import getLogger, config as logging_config, INFO

from config.log import LOGGING, LOGGING_PATH
from user import User, UserAlreadyLoggedInException, NoSuchUserException



class NoSuchCmdException(Exception):
    pass


class ParseError(Exception):
    pass


SOCKETS = []

# dict {username: <User> instance}
USERS = {}

CMD_LOGIN = 'LOGIN'
CMD_LOGOUT = 'LOGOUT'
CMD_STATUS = 'STATUS'
CMD_INVITE = 'INVITE'
CMD_SEND = 'SEND'
CMD_LEAVE = 'LEAVE'

CMDS = [CMD_LOGIN, CMD_LOGOUT, CMD_INVITE, CMD_SEND, CMD_LEAVE, CMD_STATUS]
CMD_RE = re.compile('^(?P<cmd>%s)\s?(?P<param1>\S*)?\s?(?P<param2>".*")?' % ('|'.join(CMDS)))

"""
Scenario:
LOGIN userX
INVITE userY
SEND userY "Hi,Y"
INVITE userZ
SEND userZ "Hi,Z"
SEND userY "I have Z in other chat!"
STATUS
LEAVE userY
LEAVE userZ
LOGOUT
"""


def service_msg(conn, msg):
    return conn.send(("=== %s ===\n" % msg).encode('utf-8'))


def get_user_by_conn(conn, notify=True):
    for u in USERS.values():
        if u.conn == conn:
            return u
    if notify:
        conn.send(b'===You are not logged in!===\n')
    raise NoSuchUserException(conn)


def safe_get_user_by_name(name):
    try:
        user = USERS[name]
    except KeyError:
        print('No such logged user: %s' % name)
        user = None
    return user


def handle_cmd(conn, cmd, params):
    if cmd == CMD_LOGIN:
        name = params[0]
        if not name:
            service_msg(conn, "Invalid username: '%s'" % name)
            return
        if name in USERS:
            raise UserAlreadyLoggedInException(name)
        try:
            u = get_user_by_conn(conn, False)
        except NoSuchUserException:
            USERS[name] = User(conn, name)
            USERS[name].login()
            return
        service_msg(conn, "You already logged in as %s" % u.name)
    elif cmd == CMD_LOGOUT:
        user = get_user_by_conn(conn)
        if user:
            user.logout()
            del USERS[user.name]
    elif cmd == CMD_INVITE:
        starter = get_user_by_conn(conn)
        name_to_chat = params[0]
        user_to_chat = safe_get_user_by_name(name_to_chat)
        if user_to_chat:
            starter.invite(user_to_chat)
        else:
            service_msg(conn, "No such user: @%s" % name_to_chat)
    elif cmd == CMD_SEND:
        sender = get_user_by_conn(conn)
        name_to_send = params[0]
        msg = params[1]
        user_to_send = safe_get_user_by_name(name_to_send)
        if user_to_send:
            sender.send_to(user_to_send, msg)
        else:
            service_msg(conn, "No such user: @%s" % name_to_send)
    elif cmd == CMD_LEAVE:
        stopper = get_user_by_conn(conn)
        name_to_stop = params[0]
        user_to_stop = safe_get_user_by_name(name_to_stop)
        if user_to_stop:
            stopper.leave_chat(user_to_stop)
        else:
            service_msg(conn, "No such user: @%s" % name_to_stop)
    elif cmd == CMD_STATUS:
        user = get_user_by_conn(conn)
        user.status()
    else:
        raise NoSuchCmdException(cmd)


def parse_data(data):
    data = data.decode('utf-8')
    cmd_match = CMD_RE.match(data)
    if cmd_match:
        g = cmd_match.groups()
        return g[0], g[1:]
    else:
        raise ParseError('Unable to parse: %s' % data)


def server(host='127.0.0.1', port=9090):
    _logger = getLogger('server')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)

    SOCKETS.append(server_socket)
    _logger.info("Starting server on {}:{}".format(host, port))

    while True:

        readl, writel, errl = select.select(SOCKETS, [], [], 0)

        for sock in readl:
            # a new connection request received
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKETS.append(sockfd)
                _logger.info("Client (%s, %s) connected", (addr[0], addr[1]))

            # a message from a client, not a new connection
            else:
                try:
                    data = sock.recv(4096)
                    if data:
                        try:
                            cmd, params = parse_data(data)
                        except ParseError as e:
                            sock.send(b'Unable to parse: ' + repr(data).encode('utf-8') + b'\n')
                            raise e
                        handle_cmd(sock, cmd, params)
                    else:
                        if sock in SOCKETS:
                            SOCKETS.remove(sock)
                        else:
                            raise Exception('WTF?')
                except Exception:
                    _logger.error(traceback.format_exc())
                    continue


if __name__ == '__main__':
    import os
    if not os.path.exists(LOGGING_PATH):
        os.makedirs(LOGGING_PATH)
    logging_config.dictConfig(LOGGING)
    server()

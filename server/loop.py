import select
import socket
import traceback
import logging

from server.client import Client
from server.messages import parse_data, ParseError, NormalMessage, PayloadMessage, ErrorMessage, UnknownCommand
from server.messages import CMD_LOGIN, CMD_LOGOUT
from server.models.user import InvalidUserCredentials


log = logging.getLogger('loop')

# dict {socket: <Client> instance}
CLIENTS = {}


def handle_message(client, msg):
    if isinstance(msg, NormalMessage):
        if msg.cmd == CMD_LOGIN:
            if len(msg.params) != 2:
                raise InvalidUserCredentials()
            client.login_as(msg.params[0], msg.params[1])
        if msg.cmd == CMD_LOGOUT:
            client.logout()
    elif isinstance(msg, PayloadMessage):
        pass
    elif isinstance(msg, ErrorMessage):
        pass


def run_server(host='127.0.0.1', port=9090):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)

    CLIENTS[server_socket] = None
    log.info("Starting server on {host}:{port}".format(host=host, port=port))

    while True:

        readl, writel, errl = select.select(CLIENTS.keys(), [], [], 0)

        for sock in readl:
            # a new connection request received
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                CLIENTS[sockfd] = Client(sockfd)
                log.info("Client ({host}:{port}) connected".format(host=addr[0], port=addr[1]))
            # a message from a client, not a new connection
            else:
                client = None
                try:
                    data = sock.recv(4096)
                    client = CLIENTS[sock]
                    if data:
                        msg = parse_data(data)
                        handle_message(CLIENTS[sock], msg)
                    else:
                        if sock in CLIENTS:
                            log.warning('Deleting {socket} from connections...'.format(socket=sock))
                            del CLIENTS[sock]
                        else:
                            raise Exception('WTF?')
                except Exception as e:
                    log.error(traceback.format_exc())
                    client.send(ErrorMessage(err_code=repr(repr(e).encode('utf-8'))))
                    continue


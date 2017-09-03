import select
import socket
import traceback
import logging

from server.client import Client
from server.messages import parse_data, ParseError, NormalMessage, PayloadMessage, ErrorMessage, UnknownCommand
from server.messages import CMD_LOGIN, CMD_LOGOUT
from server.models.user import InvalidUserCredentials


log = logging.getLogger('loop')


class MessServer:

    def __init__(self, port=9090):
        self.host = '127.0.0.1'
        self.port = port
        self.clients = {}  # dict {socket: <Client> instance}
        self.socket = None

    def setup(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)

        self.clients[self.socket] = None
        log.info("Starting server on {host}:{port}".format(host=self.host, port=self.port))

    def handle_message(self, client, msg):
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

    def run(self):
        self.setup()
        while True:

            readl, writel, errl = select.select(self.clients.keys(), [], [], 0)

            for sock in readl:
                # a new connection request received
                if sock == self.socket:
                    sockfd, addr = self.socket.accept()
                    self.clients[sockfd] = Client(sockfd)
                    log.info("Client ({host}:{port}) connected".format(host=addr[0], port=addr[1]))
                # a message from a client, not a new connection
                else:
                    client = None
                    try:
                        data = sock.recv(4096)
                        client = self.clients[sock]
                        if data:
                            msg = parse_data(data)
                            self.handle_message(self.clients[sock], msg)
                        else:
                            if sock in self.clients:
                                log.warning('Deleting {socket} from connections...'.format(socket=sock))
                                del self.clients[sock]
                            else:
                                raise Exception('WTF?')
                    except Exception as e:
                        log.error(traceback.format_exc())
                        client.send(ErrorMessage(err_code=repr(repr(e).encode('utf-8'))))
                        continue

    def stop(self):
        pass

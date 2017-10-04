import selectors
import socket
import traceback
import logging

from server.client import Client
from server.messages import ErrorMessage


log = logging.getLogger('loop')


class MessServer:

    def __init__(self, port=9090):
        self.host = '127.0.0.1'
        self.port = port
        self.clients = {}  # dict {socket: <Client> instance}
        self.socket = None
        self._running = False
        self.selector = selectors.DefaultSelector()

    def register_client(self, conn):
        """
        Register new client
        :param conn: connection to register as a client
        :return: None
        """
        log.info("Register new client: {fileno}".format(fileno=conn.fileno()))
        self.clients[conn.fileno()] = Client(conn, self)

    def unregister_client(self, conn):
        """
        Delete client from
        :param conn: connection to delete from clients
        :return: None
        """
        log.info("Unregister client: {fileno}".format(fileno=conn.fileno()))
        if self.clients[conn.fileno()].user:
            self.clients[conn.fileno()].logout()
        del self.clients[conn.fileno()]

    def on_accept(self, sock, mask):
        """
        Callback for new connections

        :param sock: socket to accept and register as client
        :param mask
        :return: None
        """
        new_connection, addr = self.socket.accept()
        log.info('accept({})'.format(addr))
        new_connection.setblocking(False)
        self.selector.register(fileobj=new_connection,
                               events=selectors.EVENT_READ,
                               data=self.on_read)
        self.register_client(new_connection)

    def on_read(self, conn, mask):
        """
        Callback for read events
        :param conn: connection to read from
        :param mask:
        :return: None
        """
        client = self.clients[conn.fileno()]
        try:
            data = conn.recv(1024)
            if data:
                log.info('got data from {}: {!r}'.format(conn.getpeername(), data))
                client.recv(data)
            else:
                self.on_close(conn)
        except ConnectionResetError:
            self.on_close(conn)
        except Exception as e:
            log.error(traceback.format_exc())
            client.send(ErrorMessage(err_code=repr(repr(e).encode('utf-8'))))

    def on_error(self, conn):
        """
        Handle error on connection
        :param conn:
        :return: None
        """
        pass

    def on_close(self, conn):
        """
        Close connection and delete client
        :param conn: connection to close
        :return: None
        """
        log.info('closing connection to {0}'.format(conn.getpeername()))
        self.unregister_client(conn)
        self.selector.unregister(conn)
        conn.close()

    def setup(self):
        """
        Setup server, init server socket
        :return: None
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)

        self.clients[self.socket.fileno()] = "SERVER"
        self.selector.register(fileobj=self.socket,
                               events=selectors.EVENT_READ,
                               data=self.on_accept)
        self._running = True
        log.info("Server({selector_impl}) listen on {host}:{port}".format(selector_impl=type(self.selector),
                                                                          host=self.host,
                                                                          port=self.port))

    def run(self):
        """
        Infinite loop to handle incoming events
        :return: None
        """
        self.setup()

        while self._running:
            events = self.selector.select()

            for key, mask in events:
                try:
                    handler = key.data
                    handler(key.fileobj, mask)
                except Exception:
                    log.error(traceback.format_exc())
                    continue

    def stat(self):
        """
        Return server client statistics
        :return: string from clients dictionary
        """
        return str(self.clients)

    def stop(self):
        """
        Stop server
        :return: None
        """
        for client in self.clients:
            client.send(ErrorMessage(err_code=repr("Server is stopping...".encode('utf-8'))))
            client_conn = client.conn
            self.unregister_client(client.conn)
            self.on_close(client_conn)
        self.selector.close()
        self._running = False


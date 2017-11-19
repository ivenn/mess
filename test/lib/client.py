import socket
import protocol.messages


class TestClient:

    def __init__(self):
        self.__connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

    def __repr__(self):
        return "TestClient(sock)".format(sock=self.sock)

    @property
    def connected(self):
        return self.__connected is not False

    def connect(self, host, port):
        self.sock.connect((host, port))
        self.__connected = (host, port)

    def send(self, msg):
        if isinstance(msg, protocol.messages.Message):
            msg = msg.as_bytes()
        elif isinstance(msg, str):
            msg = msg.encode('utf-8')
        elif not isinstance(msg, bytes):
            raise ValueError()

        self.sock.send(msg)

    def recv(self, timeout=5):
        self.sock.settimeout(timeout)
        data = self.sock.recv(1024)
        return data

    def disconnect(self):
        if not self.connected:
            return
        self.sock.close()
        self.__connected = False


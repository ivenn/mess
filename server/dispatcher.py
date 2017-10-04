from server.messages import NormalMessage, PayloadMessage, ErrorMessage, ServiceMessage
from server.messages import CMD_LOGIN, CMD_LOGOUT, CMD_SERVICE, CMD_FRIENDS, CMD_MESSAGE
import server.client


class MessageDispatcher:

    def __init__(self):
        pass

    def dispatch(self, client, msg):
        """
        Dispatch messages to client methods
        """
        if isinstance(msg, NormalMessage):
            if msg.cmd == CMD_LOGIN:
                if len(msg.params) != 2:
                    raise server.client.InvalidUserCredentials()
                client.login_as(msg.params[0], msg.params[1])
            elif msg.cmd == CMD_LOGOUT:
                client.logout()
            elif msg.cmd == CMD_FRIENDS:
                client.get_friends()
        elif isinstance(msg, PayloadMessage):
            if msg.cmd == CMD_MESSAGE:
                client.send_message_to(msg)
        elif isinstance(msg, ErrorMessage):
            pass
        elif isinstance(msg, ServiceMessage):
            if msg.cmd == CMD_SERVICE:
                return client.send(client.server.stat())

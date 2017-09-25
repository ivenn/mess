import logging

"""
All messages should start with 3 letter command name

##### NORMAL MASSAGES:
- USR - login - [client >> server]
- OUT - logout - [client >> server]
- ADD - add user to client list - [client >> server]
- LST - get contact list from server - [client >> server]
- CHG - change info about new status of users - [client >> server][server >> client]
- ACK - acknowledgement message - [client >> server][server >> client]

##### PAYLOAD MESSAGES
- MSG - send message with payload - [client >> server][server >> client]

##### ERROR MESSAGES
- ERR - error response

##### SERVICE MESSAGES
- SRV - server info

"""

CMD_LOGIN = 'USR'
CMD_LOGOUT = 'OUT'
CMD_ADD_CONTACT = 'ADD'
CMD_CONTACT_LIST = 'LST'
CMD_CHANGE_STATUS = 'CHG'
CMD_MSG_ACK = 'ACK'

CMD_MESSAGE = 'MSG'

CMD_ERROR = 'ERR'

CMD_SERVICE = 'SRV'

NORMAL_CMDS = [CMD_LOGIN, CMD_LOGOUT, CMD_ADD_CONTACT, CMD_CONTACT_LIST, CMD_CHANGE_STATUS, CMD_MSG_ACK]
PAYLOAD_CMDS = [CMD_MESSAGE, ]
ERROR_CMDS = [CMD_ERROR, ]
SERVICE_CMDS = [CMD_SERVICE, ]

CMDS = NORMAL_CMDS + PAYLOAD_CMDS + ERROR_CMDS + SERVICE_CMDS

log = logging.getLogger('messages')


class ParseError(Exception):
    pass


class UnknownCommand(Exception):
    pass


class Message:

    SEPARATOR_SYMBOL = b' '
    SEPARATOR_SYMBOL_STR = ' '

    SPLIT_SEQUENCE = b'||'
    SPLIT_SEQUENCE_STR = '||'

    TERM_SEQUENCE = b'..'
    TERM_SEQUENCE_STR = '..'

    def __init__(self, transaction_id=None):
        self.tr_id = transaction_id

    def as_bytes(self):
        raise NotImplementedError()


class NormalMessage(Message):
    """
    Template:
    CMD TR_ID PARAM_1 PARAM_2 PARAM_N<TERM_SEQUENCE>
    """

    def __init__(self, cmd, params, transaction_id=None):
        self.cmd = cmd
        self.params = params
        super().__init__(transaction_id)

    def __repr__(self):
        return "NormalMessage(cmd: %s, params: %s)" % (self.cmd, self.params)

    def as_bytes(self):
        msg = "{cmd} {params}{term_seq}".format(cmd=self.cmd,
                                                params=' '.join(self.params),
                                                term_seq=self.TERM_SEQUENCE_STR)
        msg = msg.encode('utf-8')
        return msg

    @staticmethod
    def from_string(str_msg):
        splitted = str_msg.split(Message.SEPARATOR_SYMBOL_STR)

        cmd = splitted[0]
        params = splitted[1:] if len(splitted) > 1 else []
        transaction_id = 0

        return NormalMessage(cmd, params, transaction_id)


class PayloadMessage(Message):
    """
    Template:
    CMD TD_ID PARAM_1 PARAM_2 PARAM_N PAYLOAD_SIZE<SPLIT_SEQUENCE>
    <---------------   PAYLOAD   --------------->  <TERM_SEQUENCE>
    """

    def __init__(self, cmd, params, payload, transaction_id=None):
        self.cmd = cmd
        self.params = params
        self.payload = payload
        super().__init__(transaction_id)

    def as_bytes(self):
        pass

    @staticmethod
    def from_string(str_msg):
        pass


class ErrorMessage(Message):
    """
    Template:
    CMD TD_ID ERR_CODE<TERM_SEQUENCE>
    """

    def __init__(self, transaction_id=None, cmd=CMD_ERROR, err_code='ERR_CODE'):
        self.cmd = cmd
        self.code = err_code  # temporarily used for error description
        super().__init__(transaction_id)

    def as_bytes(self):
        msg = "{cmd} {code}{term_seq}".format(cmd=self.cmd,
                                              code=self.code,
                                              term_seq=self.TERM_SEQUENCE_STR)
        msg = msg.encode('utf-8')
        return msg

    @staticmethod
    def from_string(str_msg):
        splitted = str_msg.split(Message.SEPARATOR_SYMBOL_STR)
        tr_id = 0
        cmd = splitted[0]
        code = 0
        return ErrorMessage(tr_id, cmd, code)


class ServiceMessage(Message):
    """
    Template:
    CMD TD_ID<TERM_SEQUENCE>
    """

    def __init__(self, transaction_id=None, cmd=CMD_ERROR):
        self.cmd = cmd
        super().__init__(transaction_id)

    def __repr__(self):
        return "ServiceMessage(cmd: %s)" % self.cmd

    def as_bytes(self):
        msg = "{cmd}{term_seq}".format(cmd=self.cmd,
                                       term_seq=self.TERM_SEQUENCE_STR)
        msg = msg.encode('utf-8')
        return msg

    @staticmethod
    def from_string(str_msg):
        splitted = str_msg.split(Message.SEPARATOR_SYMBOL_STR)
        tr_id = 0
        cmd = splitted[0]
        return ServiceMessage(tr_id, cmd)


class DataBuffer:

    def __init__(self):
        self._data_buffer = b""

    def __repr__(self):
        return "MsgHandler(buffer:{data_buffer})".format(data_buffer=self._data_buffer)

    @property
    def data_buffer(self):
        return self._data_buffer

    def push(self, data):
        """
        Put data in buffers and returns list of bytes strings to parse
        """
        raw_messages = []
        if data == b'\n':
            return raw_messages  # ignore single newline symbols
        self._data_buffer += data
        log.info("Got {data} in data buffer".format(data=self._data_buffer))
        if Message.TERM_SEQUENCE in self._data_buffer:
            split_data = self._data_buffer.split(Message.TERM_SEQUENCE)
            self._data_buffer = split_data[-1]
            raw_messages = split_data[:-1]
        return raw_messages

    def flush(self):
        self._data_buffer = b""


class DataParser:

    def __init__(self):
        pass

    def parse(self, data):
        """
        Parse bytes data to Message
        """
        log.info("Parsing {data}".format(data=data))
        assert Message.TERM_SEQUENCE not in data
        data = data.decode('utf-8').strip()
        cmd = data[:3]

        if cmd in NORMAL_CMDS:
            msg = NormalMessage.from_string(data)
        elif cmd in PAYLOAD_CMDS:
            msg = PayloadMessage.from_string(data)
        elif cmd in ERROR_CMDS:
            msg = ErrorMessage.from_string(data)
        elif cmd in SERVICE_CMDS:
            msg = ServiceMessage.from_string(data)
        else:
            if cmd not in CMDS:
                raise UnknownCommand(cmd)
            else:
                raise ParseError(cmd, data)
        log.info(msg)
        return msg


class MessageDispatcher:

    def __init__(self):
        pass

    def dispatch(self, client, msg):
        """
        Dispatch messages to client methods
        """
        if isinstance(msg, NormalMessage):
            client.handle_normal_msg(msg)
        elif isinstance(msg, PayloadMessage):
            pass
        elif isinstance(msg, ErrorMessage):
            pass
        elif isinstance(msg, ServiceMessage):
            if msg.cmd == CMD_SERVICE:
                return client.send(client.server.stat())


if __name__ == '__main__':
    test_msgs = ['']
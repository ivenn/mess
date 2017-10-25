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
CMD_FRIENDS = 'FRD'
CMD_CHANGE_STATUS = 'CHG'
CMD_MSG_ACK = 'ACK'

CMD_INFO = 'INF'
CMD_MESSAGE = 'MSG'

CMD_ERROR = 'ERR'

CMD_SERVICE = 'SRV'

NORMAL_CMDS = [CMD_LOGIN,
               CMD_LOGOUT,
               CMD_ADD_CONTACT,
               CMD_FRIENDS,
               CMD_CHANGE_STATUS,
               CMD_MSG_ACK, ]

PAYLOAD_CMDS = [CMD_MESSAGE,
                CMD_INFO, ]

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

    def __init__(self, cmd, params=[], transaction_id=None):
        self.cmd = cmd
        self.params = params
        super().__init__(transaction_id)

    def __repr__(self):
        return "NormalMessage(cmd: %s, params: %s)" % (self.cmd, self.params)

    def __eq__(self, other):
        if self.cmd == other.cmd and self.params == self.params:
            return True
        else:
            return False

    def as_bytes(self):
        msg_template = "{cmd} {params}{term_seq}\n"
        msg = msg_template.format(cmd=self.cmd,
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
    CMD TR_ID PARAM_1 PARAM_2 PARAM_N PAYLOAD_SIZE<SPLIT_SEQUENCE>
    <---------------   PAYLOAD   -----------------><TERM_SEQUENCE>
    """

    def __init__(self, cmd, params, payload, transaction_id=None):
        self.cmd = cmd
        self.params = params
        self.payload = payload
        super().__init__(transaction_id)

    def as_bytes(self):
        msg_template = "{cmd} {params} {payload_size}{split_seq}{payload}{term_seq}\n"
        msg = msg_template.format(cmd=self.cmd,
                                  params=' '.join(self.params),
                                  payload_size=len(self.payload),
                                  split_seq=self.SPLIT_SEQUENCE_STR,
                                  payload=self.payload,
                                  term_seq=self.TERM_SEQUENCE_STR)
        msg = msg.encode('utf-8')
        return msg

    @staticmethod
    def from_string(str_msg):
        service_part, payload = str_msg.split(Message.SPLIT_SEQUENCE_STR)
        service_part_splitted = service_part.split(Message.SEPARATOR_SYMBOL_STR)
        cmd = service_part_splitted[0]
        params = service_part_splitted[1:-1]
        payload_size = service_part_splitted[-1]
        return PayloadMessage(cmd, params, payload)


class ErrorMessage(Message):
    """
    Template:
    CMD TR_ID ERR_CODE<TERM_SEQUENCE>
    """

    def __init__(self, transaction_id=None, cmd=CMD_ERROR, err_code='ERR_CODE'):
        self.cmd = cmd
        self.code = err_code  # temporarily used for error description
        super().__init__(transaction_id)

    def __repr__(self):
        return "ErrorMessage(cmd={cmd}, code={code})".format(cmd=self.cmd, code=self.code)

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
    CMD TR_ID<TERM_SEQUENCE>
    """

    def __init__(self, transaction_id=None, cmd=CMD_ERROR):
        self.cmd = cmd
        super().__init__(transaction_id)

    def __repr__(self):
        return "ServiceMessage(cmd: %s)" % (self.cmd)

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


if __name__ == '__main__':
    test_msgs = ['']

"""
All messages should start with 3 letter command name


##### NORMAL MASSAGES:
CMD LIST:
- USR - login - [client >> server]
- OUT - logout - [client >> server]
- ADD - add user to client list - [client >> server]
- LST - get contact list from server - [client >> server]
- CHG - change info about new status of users - [client >> server][server >> client]
- ACK - acknowledgement message - [client >> server][server >> client]

>[CMD] TR_ID PARAM_1 PARAM_2 ... PARAM_N\n\n



##### PAYLOAD MESSAGES
CMD LIST:
- MSG - send message with payload - [client >> server][server >> client]

>[CMD] TR_ID PARAM_1 PARAM_2 ... PARAM_N PAYLOAD_SIZE\n\n
>-------------------PAYLOAD------------------------



##### ERROR MESSAGES
CMD LIST:
- ERR - error response

>[ERR] TR_ID CODE\n\n

"""

CMD_LOGIN = 'USR'
CMD_LOGOUT = 'OUT'
CMD_ADD_CONTACT = 'ADD'
CMD_CONTACT_LIST = 'LST'
CMD_CHANGE_STATUS = 'CHG'
CMD_MSG_ACK = 'ACK'

CMD_MESSAGE = 'MSG'

CMD_ERROR = 'ERR'

NORMAL_CMDS = [CMD_LOGIN, CMD_LOGOUT, CMD_ADD_CONTACT, CMD_CONTACT_LIST, CMD_CHANGE_STATUS, CMD_MSG_ACK]
PAYLOAD_CMDS = [CMD_MESSAGE, ]
ERROR_CMDS = [CMD_ERROR, ]

TERM_SEQUENCE = '\n\n'


class ParseError(Exception):
    pass


class Message:

    def __init__(self, transaction_id=None):
        self.tr_id = transaction_id


class NormalMessage(Message):

    def __init__(self, cmd, params, transaction_id=None):
        self.cmd = cmd
        self.params = params
        super().__init__(transaction_id)

    def __repr__(self):
        return "NormalMessage(cmd: %s, params: %s)" % (self.cmd, self.params)


class PayloadMessage(Message):

    def __init__(self, cmd, params, payload, transaction_id=None):
        self.cmd = cmd
        self.params = params
        self.payload = payload
        super().__init__(transaction_id)


class ErrorMessage(Message):

    def __init__(self, transaction_id, cmd, err_code):
        self.cmd = cmd
        self.code = err_code
        super().__init__(transaction_id)


def parse_msg(data):
    splitted_data = data.split(TERM_SEQUENCE)[0].split()
    cmd = splitted_data[0]
    tr_id = 0  # splitted_data[1]
    params = splitted_data[1:]

    return NormalMessage(cmd, params, tr_id)


def parse_payload_msg(data):
    splitted_data = data.split(TERM_SEQUENCE)

    srv_data = splitted_data[0].split()
    payload = splitted_data[1]

    cmd = srv_data[0]
    tr_id = srv_data[1]
    params = srv_data[2:-1]
    payload_len = srv_data[-1]

    print(len(payload) == payload_len)

    return PayloadMessage(cmd, params, payload, tr_id)


def parse_err_msg(data):
    cmd, tr_id, code = (data[:-2]).split()
    return ErrorMessage(tr_id, cmd, code)


def parse_data(data):
    """
    get raw data(bytes) and returns Message instance
    :param data: bytes
    :return:
    """
    data = data.decode('utf-8')
    cmd = data[:3]

    if cmd in NORMAL_CMDS:
        msg = parse_msg(data)
        print(msg)
        return msg
    elif cmd in PAYLOAD_CMDS:
        return parse_payload_msg(data)
    elif cmd in ERROR_CMDS:
        return parse_err_msg(data)
    else:
        raise ParseError(data, cmd)


if __name__ == '__main__':
    test_msgs = ['']
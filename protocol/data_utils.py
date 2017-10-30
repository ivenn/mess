import logging

from protocol.messages import Message, NormalMessage, PayloadMessage, ErrorMessage, ParseError
from protocol.messages import NORMAL_CMDS, PAYLOAD_CMDS, ERROR_CMDS, CMDS


log = logging.getLogger(__name__)


class UnknownCommand(Exception):
    pass


class DataBuffer:

    def __init__(self):
        self._data = b""

    def __repr__(self):
        return "DataBuffer:{data_buffer})".format(data_buffer=self._data)

    @property
    def data(self):
        return self._data

    def push(self, data):
        """
        Put data in buffers and returns list of bytes strings to parse
        """
        raw_messages = []
        if data == b'\n':
            return raw_messages  # ignore single newline symbols
        self._data += data
        log.info("Got {data} in data buffer".format(data=self._data))
        if Message.TERM_SEQUENCE in self._data:
            split_data = self._data.split(Message.TERM_SEQUENCE)
            self._data = split_data[-1]
            raw_messages = split_data[:-1]
        return raw_messages

    def flush(self):
        self._data = b""


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
        else:
            if cmd not in CMDS:
                raise UnknownCommand(cmd)
            else:
                raise ParseError(cmd, data)
        return msg

import collections
import logging


log = logging.getLogger(__name__)


class DictProxy(collections.MutableMapping):

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value
        log.info(str(self.store))

    def __delitem__(self, key):
        del self.store[key]
        log.info(str(self.store))

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


ONLINE_USERS = DictProxy()

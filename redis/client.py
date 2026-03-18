"""In-memory redis client stub for local tests.

Provides a `Redis` class with `from_url`, `delete`, `keys`, `get`, `lpush`, `set`.
This is a tiny convenience stub to make tests importable without installing
the `redis` package or a running Redis server.
"""
import re
from urllib.parse import urlparse

class Redis:
    _store = {}

    def __init__(self, url=None, decode_responses=False, **kwargs):
        # Accept extra kwargs (password, socket_timeout, etc.) for compatibility
        self.decode = decode_responses
        self.url = url
        if url:
            p = urlparse(url)
            try:
                self.db_index = int(p.path.lstrip('/')) if p.path else 0
            except Exception:
                self.db_index = 0
        else:
            self.db_index = 0

    @classmethod
    def from_url(cls, url, decode_responses=False, **kwargs):
        # Accept and ignore additional redis.from_url kwargs (e.g., password)
        return cls(url=url, decode_responses=decode_responses, **kwargs)

    def _key(self, k):
        return f"db:{self.db_index}:{k}"

    def delete(self, *keys):
        removed = 0
        for k in keys:
            kk = self._key(k)
            if kk in self._store:
                del self._store[kk]
                removed += 1
        return removed

    def keys(self, pattern="*"):
        pat = re.escape(pattern).replace(r"\*", ".*")
        regex = re.compile(f"^{pat}$")
        prefix = f"db:{self.db_index}:"
        out = []
        for k in list(self._store.keys()):
            if not k.startswith(prefix):
                continue
            short = k[len(prefix):]
            if regex.match(short):
                out.append(short)
        return out

    def get(self, key):
        return self._store.get(self._key(key))

    def set(self, key, value, **kwargs):
        # accept extra kwargs like ex for compatibility
        self._store[self._key(key)] = value
        return True

    def lpush(self, key, value):
        kk = self._key(key)
        lst = self._store.get(kk)
        if lst is None:
            lst = []
        if not isinstance(lst, list):
            lst = [lst]
        lst.insert(0, value)
        self._store[kk] = lst
        return len(lst)

    def rpush(self, key, value):
        kk = self._key(key)
        lst = self._store.get(kk)
        if lst is None:
            lst = []
        if not isinstance(lst, list):
            lst = [lst]
        lst.append(value)
        self._store[kk] = lst
        return len(lst)

    # Additional helpers used by the codebase
    def ping(self):
        return True

    def rpop(self, key):
        kk = self._key(key)
        lst = self._store.get(kk)
        if not lst:
            return None
        if isinstance(lst, list):
            val = lst.pop() if lst else None
            self._store[kk] = lst
            return val
        else:
            v = lst
            del self._store[kk]
            return v

    def brpop(self, keys, timeout=0):
        # keys: list of queue names. Return (queue_name, item) or None
        for k in keys:
            kk = self._key(k)
            lst = self._store.get(kk)
            if lst and isinstance(lst, list) and len(lst) > 0:
                # pop from right
                item = lst.pop()
                self._store[kk] = lst
                return (k, item)
        return None

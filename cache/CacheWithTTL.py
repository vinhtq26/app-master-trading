import time
class CacheWithTTL:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key in self.cache:
            value, timestamp, ttl = self.cache[key]
            if time.time() - timestamp < ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key, value, ttl):
        self.cache[key] = (value, time.time(), ttl)

cache = CacheWithTTL()

# TTL cho từng period
PERIOD_TTL = {
    "15m": 300,    # 5 phút
    "1h": 600,     # 10 phút
    "4h": 1800,    # 30 phút
    "1d": 3600     # 1 giờ
}

class MemoryStore:

    def __init__(self):
        self.storage = {}

    def save(self, key, value):
        self.storage[key] = value

    def get(self, key):
        return self.storage.get(key)

    def get_all(self):
        return self.storage
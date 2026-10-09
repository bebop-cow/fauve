import os

class Store:
    def __init__(self, root):
        self.root = root
        self.cache = {}
        self.log_path = os.path.join(root, "log.txt")
        os.makedirs(root, exist_ok=True)

    def _path(self, key):
        return os.path.join(self.root, key)

    def save(self, key, text):
        path = self._path(key)
        with open(path, "w") as f:
            f.write(text)
        self.cache[key] = text
        with open(self.log_path, "a") as f:
            f.write(key + "\n")        

    def erase(self, key):
        self.cache.pop(key, None)
        path = self._path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
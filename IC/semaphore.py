from threading import Lock


class Semaphore(object):
    def __init__(self, max, value):
        self.value = value
        self._max = max

    def up(self):
        lock = Lock()
        with lock:
            if self.value < self._max:
                self.value += 1
                return True
            else:
                return False

    def down(self):
        lock = Lock()
        with lock:
            if self.value > 0:
                self.value -= 1
                return True
            else:
                return False

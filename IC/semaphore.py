from threading import Lock


class Semaphore(object):
    def __init__(self, max, value):
        self._value = value
        self._max = max

    def up(self):
        lock = Lock()
        with lock:
            if self._value < self._max:
                self._value += 1
                return True
            else:
                return False

    def down(self):
        lock = Lock()
        with lock:
            if self._value > 0:
                self._value -= 1
                return True
            else:
                return False

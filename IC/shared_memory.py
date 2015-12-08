from threading import Lock


class SharedMemory(object):
    def __init__(self, page_size, page_count):
        self._page_size = page_size
        self._page_count = page_count
        self._keys = [int for _ in range(page_count)]
        self._pages_bitmap = [False for _ in range(page_count)]
        self._pages = [list() for _ in range(page_count)]

    def _new_page(self, key):
        try:
            free_page = self._pages_bitmap.index(False)
            self._keys[free_page] = key
            self._pages_bitmap[free_page] = True
            self._pages[free_page] = [0 for _ in range(self._page_size)]
            return True
        except ValueError:
            return False

    def get_page(self, key):
        lock = Lock()
        with lock:
            try:
                return self._pages[self._keys.index(key)]
            except ValueError:
                if self._new_page(key):
                    return self.get_page(key)
                else:
                    return None

    def clear_page(self, key):
        lock = Lock()
        with lock:
            try:
                index = self._keys.index(key)
                self._pages_bitmap[index] = False
                self._keys[index] = None
                return True
            except ValueError:
                return False

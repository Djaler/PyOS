from struct import pack, unpack, calcsize


class InodeMap(object):
    def __init__(self, list):
        self._list = list

    def set(self, index, value):
        self._list[index] = value

    def write(self, inode_map_offset, file):
        file.seek(inode_map_offset)
        file.write(pack('%d?' % len(self._list), *self._list))

    def get_free_inode(self):
        return self._list.index(True)

    @staticmethod
    def empty(size):
        return InodeMap([True] * size)

    @staticmethod
    def read(inode_num, inode_map_offset, file):
        format = '%d?' % inode_num
        file.seek(inode_map_offset)
        return InodeMap(list(unpack(format, file.read(calcsize(format)))))

from struct import pack, unpack, calcsize
from time import time


class Inode(object):
    format = '7i'
    _size = calcsize(format)

    def __init__(self, id, uid=0, perm=0, size=0, ctime=0, mtime=0,
                 first_cluster=-1):
        self._id = id
        self._uid = uid
        self._perm = perm
        self._size = size
        self._ctime = ctime
        self._mtime = mtime
        self._first_cluster = first_cluster

    def pack(self):
        return pack(self.format, self._id, self._uid, self._perm, self._size,
                    self._ctime, self._mtime, self._first_cluster)

    def set_permissions(self, owner_read, owner_write, other_read,
                        other_write):
        self._perm = 0
        if owner_read:
            self._perm += 20
        if owner_write:
            self._perm += 10
        if other_read:
            self._perm += 2
        if other_write:
            self._perm += 1

    def set_mtime(self):
        self._mtime = int(time())

    @property
    def owner_read(self):
        return self._perm // 10 >= 2

    @property
    def owner_write(self):
        return (self._perm // 10) % 2 == 1

    @property
    def other_read(self):
        return self._perm % 10 >= 2

    @property
    def other_write(self):
        return (self._perm % 10) % 2 == 1

    @property
    def id(self):
        return self._id

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    @property
    def first_cluster(self):
        return self._first_cluster

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size

    @staticmethod
    def get_inode(inode_array_offset, file, index):
        file.seek(inode_array_offset + Inode._size * index)
        return Inode(*unpack(Inode.format, file.read(Inode._size)))

    @staticmethod
    def set_inode(inode_array_offset, file, inode):
        file.seek(inode_array_offset + Inode._size * inode.id)
        file.write(inode.pack())

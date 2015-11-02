from struct import pack, unpack, calcsize


class InodeMap(object):
    def __init__(self, list):
        self.list = list

    @staticmethod
    def empty(size):
        return InodeMap([True] * size)
    
    @staticmethod
    def read(inode_num, inode_map_offset, file):
        format = '%d?' % inode_num
        file.seek(inode_map_offset)
        return InodeMap(list(unpack(format, file.read(calcsize(format)))))

    def write(self, inode_map_offset, file):
        file.seek(inode_map_offset)
        file.write(pack('%d?' % len(self.list), *self.list))

    def get_free_inode(self):
        return self.list.index(True)

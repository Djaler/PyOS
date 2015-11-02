from struct import pack, unpack, calcsize


class InodeBitmap(object):
    def __init__(self, list):
        self.list = list

    @staticmethod
    def empty(size):
        return InodeBitmap([True] * size)
    
    @staticmethod
    def get_bitmap(inode_num, inode_bitmap_offset, file):
        format = '%d?' % inode_num
        file.seek(inode_bitmap_offset)
        return InodeBitmap(list(unpack(format, file.read(calcsize(format)))))

    def write(self, inode_bitmap_offset, file):
        file.seek(inode_bitmap_offset)
        file.write(pack('%d?' % len(self.list), *self.list))

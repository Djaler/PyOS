from struct import pack, unpack, calcsize


class FAT(object):
    def __init__(self, list):
        self.list = list

    @staticmethod
    def empty(size):
        return FAT([0] * size)

    def set_el(self, superblock, index, value):
        before = self.list[index]
        self.list[index] = value
        if before == 0 and value != 0:
            superblock.free_cluster_num -= 1
        elif before != 0 and value == 0:
            superblock.free_cluster_num += 1
    
    @staticmethod
    def get_fat(fat_size, fat_offset, file):
        format = '%di' % fat_size
        file.seek(fat_offset)
        return FAT(list(unpack(format, file.read(calcsize(format)))))

    def write(self, fat_offset, file):
        file.seek(fat_offset)
        file.write(pack('%di' % len(self.list), *self.list))

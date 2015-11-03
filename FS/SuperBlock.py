from struct import pack, unpack, calcsize


class SuperBlock(object):
    _cluster_size = 4096
    _format = '5i'
    _fat_offset = calcsize(_format)

    def __init__(self, cluster_num, free_cluster_num, inode_bitmap_offset,
                 inode_array_offset, first_cluster_offset):
        self._cluster_num = cluster_num
        self._free_cluster_num = free_cluster_num
        self._inode_map_offset = inode_bitmap_offset
        self._inode_array_offset = inode_array_offset
        self._first_cluster_offset = first_cluster_offset

    def write(self, file):
        file.seek(0)
        file.write(
            pack(self._format, self._cluster_num, self._free_cluster_num,
                 self._inode_map_offset, self._inode_array_offset,
                 self._first_cluster_offset))

    def increase_free_cluster_num(self):
        self._free_cluster_num += 1

    def decrease_free_cluster_num(self):
        self._free_cluster_num -= 1

    @staticmethod
    def default(size):
        cluster_num = size // SuperBlock._cluster_size
        free_cluster_num = 0
        inode_bitmap_offset = SuperBlock._fat_offset + cluster_num * 4
        inode_array_offset = inode_bitmap_offset + cluster_num
        first_cluster_offset = 0
        return SuperBlock(cluster_num, free_cluster_num, inode_bitmap_offset,
                          inode_array_offset, first_cluster_offset)

    @staticmethod
    def get_superblock(file):
        format = SuperBlock._format
        file.seek(0)
        return SuperBlock(*unpack(format, file.read(calcsize(format))))

    @property
    def cluster_size(self):
        return self._cluster_size

    @property
    def cluster_num(self):
        return self._cluster_num

    @property
    def free_cluster_num(self):
        return self._free_cluster_num

    @free_cluster_num.setter
    def free_cluster_num(self, free_cluster_num):
        self._free_cluster_num = free_cluster_num

    @property
    def fat_offset(self):
        return self._fat_offset

    @property
    def inode_map_offset(self):
        return self._inode_map_offset

    @property
    def inode_array_offset(self):
        return self._inode_array_offset

    @property
    def first_cluster_offset(self):
        return self._first_cluster_offset

    @first_cluster_offset.setter
    def first_cluster_offset(self, first_cluster_offset):
        self._first_cluster_offset = first_cluster_offset

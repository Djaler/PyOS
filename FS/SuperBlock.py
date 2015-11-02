from struct import pack, unpack, calcsize


class SuperBlock(object):
    cluster_size = 4096
    format = '5i'
    fat_offset = calcsize(format)

    def __init__(self, cluster_num, free_cluster_num, inode_bitmap_offset,
                 inode_array_offset, first_cluster_offset):
        self.cluster_num = cluster_num
        self.free_cluster_num = free_cluster_num
        self.inode_array_offset = inode_array_offset
        self.inode_bitmap_offset = inode_bitmap_offset
        self.first_cluster_offset = first_cluster_offset

    @staticmethod
    def default(size):
        cluster_num = size // SuperBlock.cluster_size
        free_cluster_num = 0
        inode_bitmap_offset = SuperBlock.fat_offset + cluster_num * 4
        inode_array_offset = inode_bitmap_offset + cluster_num
        first_cluster_offset = 0
        return SuperBlock(cluster_num, free_cluster_num, inode_bitmap_offset,
                          inode_array_offset, first_cluster_offset)

    @staticmethod
    def get_superblock(file):
        format = SuperBlock.format
        file.seek(0)
        return SuperBlock(*unpack(format, file.read(calcsize(format))))

    def write(self, file):
        file.seek(0)
        file.write(pack(self.format, self.cluster_num, self.free_cluster_num,
                        self.inode_bitmap_offset, self.inode_array_offset,
                        self.first_cluster_offset))

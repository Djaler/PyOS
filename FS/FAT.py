from struct import pack, unpack, calcsize
from FS.NoFreeClustersException import NoFreeClustersException


class FAT(object):
    def __init__(self, list, superblock):
        self.list = list
        self._superblock = superblock

    @staticmethod
    def empty(size, superblock):
        return FAT([0] * size, superblock)

    def set_el(self, index, value):
        before = self.list[index]
        self.list[index] = value
        if before == 0 and value != 0:
            self._superblock.free_cluster_num -= 1
        elif before != 0 and value == 0:
            self._superblock.free_cluster_num += 1
    
    @staticmethod
    def read(fat_size, fat_offset, file, superblock):
        format = '%di' % fat_size
        file.seek(fat_offset)
        return FAT(list(unpack(format, file.read(calcsize(format)))),
                   superblock)

    def write(self, fat_offset, file):
        file.seek(fat_offset)
        file.write(pack('%di' % len(self.list), *self.list))

    def get_free_cluster(self):
        try:
            return self.list.index(0)
        except ValueError:
            raise NoFreeClustersException()

    def get_clusters_chain(self, first_cluster):
        clusters = [first_cluster]

        next = self.list[first_cluster]
        while next != -1:
            clusters.append(next)
            next = self.list[next]

        return clusters

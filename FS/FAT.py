from struct import pack, unpack, calcsize
from FS.NoFreeClustersException import NoFreeClustersException


class FAT(object):
    def __init__(self, list, superblock):
        self._list = list
        self._superblock = superblock

    def set(self, index, value):
        before = self._list[index]
        self._list[index] = value
        if before == 0 and value != 0:
            self._superblock.decrease_free_cluster_num()
        elif before != 0 and value == 0:
            self._superblock.increase_free_cluster_num()

    def write(self, fat_offset, file):
        file.seek(fat_offset)
        file.write(pack('%di' % len(self._list), *self._list))

    def get_free_cluster(self):
        try:
            return self._list.index(0)
        except ValueError:
            raise NoFreeClustersException()

    def get_clusters_chain(self, first_cluster):
        clusters = [first_cluster]

        next = self._list[first_cluster]
        while next != -1:
            clusters.append(next)
            next = self._list[next]

        return clusters

    @staticmethod
    def empty(size, superblock):
        return FAT([0] * size, superblock)

    @staticmethod
    def read(fat_size, fat_offset, file, superblock):
        format = '%di' % fat_size
        file.seek(fat_offset)
        return FAT(list(unpack(format, file.read(calcsize(format)))),
                   superblock)

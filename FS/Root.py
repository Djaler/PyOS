from struct import pack, unpack
from time import time
from FS.Inode import Inode


class Root(object):
    def __init__(self, superblock, fat, file):
        self._superblock = superblock
        self._fat = fat
        self._file = file

        self._init_files_list()

    def add(self, file_name, inode):
        superblock = self._superblock
        fat = self._fat
        file = self._file

        file_name = bytes(file_name, 'utf-8')

        clusters = fat.get_clusters_chain(0)
        empty_space = None

        for cluster in clusters:
            file.seek(self._cluster_offset(cluster))
            for _ in range(superblock.cluster_size // 64):
                data = unpack('59sci', file.read(64))
                if ord(data[1]) == 0:
                    empty_space = file.tell() - 64
                    break

            if empty_space:
                break
        else:
            cluster_index = fat.get_free_cluster()

            fat.set(clusters[-1], cluster_index)
            fat.set(cluster_index, -1)
            empty_space = self._cluster_offset(cluster_index)

            root_inode = Inode.get_inode(superblock.inode_array_offset, file,
                                         0)
            root_inode.size = (len(clusters) + 1) * superblock.cluster_size
            Inode.set_inode(superblock.inode_array_offset, file, root_inode)

        file.seek(empty_space)
        file.write(pack('59sci', file_name, bytes([len(file_name)]), inode.id))

        self._list[file_name.decode()] = inode
        Inode.set_inode(superblock.inode_array_offset, file, inode)

    def read(self, file_name):
        return self._list[file_name]

    def delete(self, file_name):
        superblock = self._superblock
        fat = self._fat
        file = self._file

        file_name = bytes(file_name, 'utf-8')

        clusters = fat.get_clusters_chain(0)
        found = False
        for cluster in clusters:
            file.seek(self._cluster_offset(cluster))
            for _ in range(superblock.cluster_size // 64):
                data = unpack('59sci', file.read(64))
                length = ord(data[1])
                name = data[0][:length]
                if name == file_name:
                    file.seek(-64, 1)
                    file.write(pack('64s', bytes([0] * 64)))
                    del (self._list[file_name.decode()])
                    found = True
                    break

            if found:
                break

    def _init_files_list(self):
        superblock = self._superblock
        fat = self._fat
        file = self._file

        self._list = {}
        clusters = fat.get_clusters_chain(0)

        for cluster in clusters:
            file.seek(self._cluster_offset(cluster))
            for _ in range(superblock.cluster_size // 64):
                data = unpack('59sci', file.read(64))
                length = ord(data[1])

                if length:
                    position = file.tell()
                    self._list[data[0][:length].decode()] = Inode.get_inode(
                            superblock.inode_array_offset, file, data[2])
                    file.seek(position)

    def _cluster_offset(self, cluster_index):
        return (
            self._superblock.first_cluster_offset + cluster_index *
            self._superblock.cluster_size)

    def update_inode(self, file_name, inode):
        self._list[file_name] = inode
        Inode.set_inode(self._superblock.inode_array_offset, self._file, inode)

    @property
    def list(self):
        return self._list.copy()

    @staticmethod
    def write(superblock, fat, inode_map, file):
        now = int(time())
        inode = Inode(id=0, size=superblock.cluster_size, ctime=now, mtime=now,
                      first_cluster=0)
        Inode.set_inode(superblock.inode_array_offset, file, inode)
        inode_map.set(inode.id, False)
        fat.set(0, -1)

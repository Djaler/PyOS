import hashlib
from struct import pack, unpack
from time import time
from FS.Inode import Inode


class Root(object):
    def __init__(self, superblock, fat, file):
        self._superblock = superblock
        self._fat = fat
        self._file = file

        self._init_files_list()

    @staticmethod
    def write(superblock, fat, inode_map, file):
        file.seek(superblock.first_cluster_offset)
        file.write(pack('1024i', *[-1] * 1024))

        now = int(time())
        inode = Inode(id=0, size=4096, ctime=now, mtime=now, first_cluster=0)
        Inode.set_inode(superblock.inode_array_offset, file, inode)
        inode_map.set(inode.id, False)
        fat.set(0, -1)

    def add(self, file_name, inode):
        superblock = self._superblock
        fat = self._fat
        file = self._file

        file_name = bytes(file_name, 'utf-8')
        file_hash = int(hashlib.md5(file_name).hexdigest(), 16) % 1024
        row = superblock.first_cluster_offset + file_hash * 4
        file.seek(row)
        address = unpack('i', file.read(4))[0]

        if address == -1:
            cluster_index = fat.get_free_cluster()

            file.seek(row)
            file.write(pack('i', cluster_index))

            file.seek(self._cluster_offset(cluster_index))
            file.write(
                pack('59sci', file_name, bytes([len(file_name)]), inode.id))
            fat.set(cluster_index, -1)
        else:
            clusters = fat.get_clusters_chain(address)
            current_cluster = 0

            file.seek(self._cluster_offset(clusters[0]))
            empty_space = None
            while not empty_space:
                data = unpack('59sci', file.read(64))
                if ord(data[1]) == 0:
                    empty_space = file.tell() - 64
                    break

                if file.tell() % superblock.cluster_size != 0:
                    continue

                if current_cluster + 1 == len(clusters):
                    cluster_index = fat.get_free_clusters()

                    fat.set(clusters[-1], cluster_index)
                    fat.set(cluster_index, -1)
                    clusters.append(cluster_index)
                    file.seek(self._cluster_offset(cluster_index))

                    inode = Inode.get_inode(superblock.inode_array_offset,
                                            file, 0)
                    inode.size = len(clusters) * superblock.cluster_size
                    Inode.set_inode(superblock.inode_array_offset, file, inode)

                current_cluster += 1
                file.seek(self._cluster_offset(clusters[current_cluster]))

            file.seek(empty_space)
            file.write(
                pack('59sci', file_name, bytes([len(file_name)]), inode.id))

        self._list[file_name.decode()] = inode

    def read(self, file_name):
        return self._list[file_name]

    def delete(self, file_name):
        superblock = self._superblock
        fat = self._fat
        file = self._file

        file_name = bytes(file_name, 'utf-8')
        file_hash = int(hashlib.md5(file_name).hexdigest(), 16) % 1024
        file.seek(superblock.first_cluster_offset + file_hash * 4)
        address = unpack('i', file.read(4))[0]

        clusters = fat.get_clusters_chain(address)
        current_cluster = 0

        file.seek(self._cluster_offset(clusters[0]))
        name = ''
        while name != file_name:
            data = unpack('59sci', file.read(64))
            length = ord(data[1])
            name = data[0][:length]

            if file.tell() % superblock.cluster_size == 0 and len(
                    clusters) > current_cluster + 1:
                current_cluster += 1
                file.seek(self._cluster_offset(clusters[current_cluster]))

        file.seek(-64, 1)
        file.write(pack('64s', bytes([0] * 64)))

        del (self._list[file_name.decode()])

    def _init_files_list(self):
        superblock = self._superblock
        fat = self._fat
        file = self._file

        self._list = {}
        for row in range(1024):
            file.seek(superblock.first_cluster_offset + row * 4)
            address = unpack('i', file.read(4))[0]
            if address == -1:
                continue

            clusters = fat.get_clusters_chain(address)
            current_cluster = 0

            file.seek(self._cluster_offset(address))
            while True:
                data = unpack('59sci', file.read(64))
                length = ord(data[1])

                if length:
                    position = file.tell()
                    self._list[data[0][:length].decode()] = Inode.get_inode(
                        superblock.inode_array_offset, file, data[2])
                    file.seek(position)

                if file.tell() % superblock.cluster_size != 0:
                    continue

                if current_cluster + 1 < len(clusters):
                    current_cluster += 1
                    file.seek(self._cluster_offset(clusters[current_cluster]))
                else:
                    break

    def _cluster_offset(self, cluster_index):
        return (
            self._superblock.first_cluster_offset + cluster_index *
            self._superblock.cluster_size)

    def update_inode(self, file_name, inode):
        self._list[file_name] = inode

    @property
    def list(self):
        return self._list.copy()

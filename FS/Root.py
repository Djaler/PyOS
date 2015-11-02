import hashlib
from struct import pack, unpack
from time import time
from FS.Inode import Inode


class Root(object):
    def __init__(self):
        self.hash_table = [-1] * 1024

    def write(self, superblock, fat, inode_bitmap, inode, file):
        file.seek(superblock.first_cluster_offset)
        file.write(pack('1024i', *self.hash_table))
        inode.size = 4096
        inode.ctime = inode.mtime = int(time())
        inode.first_cluster = 0
        Inode.set_inode(superblock.inode_array_offset, file, 0, inode)
        inode_bitmap.list[inode.id] = False
        fat.set_el(0, -1)

    @staticmethod
    def add(superblock, fat, file, file_name, inode_id):
        file_name = bytes(file_name, 'utf-8')
        file_hash = int(hashlib.md5(file_name).hexdigest(), 16) % 1024
        row = superblock.first_cluster_offset + file_hash * 4
        file.seek(row)
        address = unpack('i', file.read(4))[0]

        if address == -1:
            cluster_index = fat.get_free_cluster()

            file.seek(row)
            file.write(pack('i', cluster_index))

            file.seek(Root.cluster_offset(superblock, cluster_index))
            file.write(
                pack('59sci', file_name, bytes([len(file_name)]), inode_id))
            fat.set_el(cluster_index, -1)
        else:
            clusters = fat.get_clusters_chain(address)
            current_cluster = 0

            file.seek(Root.cluster_offset(superblock, clusters[0]))
            while True:
                data = unpack('59sci', file.read(64))
                if int.from_bytes(data[1], 'big') == 0:
                    empty_space = file.tell() - 64
                    break

                if file.tell() % superblock.cluster_size != 0:
                    continue

                if current_cluster + 1 == len(clusters):
                    cluster_index = fat.get_free_clusters()

                    fat.set_el(clusters[-1], cluster_index)
                    fat.set_el(cluster_index, -1)
                    clusters.append(cluster_index)
                    file.seek(Root.cluster_offset(superblock, cluster_index))

                current_cluster += 1
                file.seek(
                    Root.cluster_offset(superblock, clusters[current_cluster]))

            file.seek(empty_space)
            file.write(
                pack('59sci', file_name, bytes([len(file_name)]), inode_id))

    @staticmethod
    def read(superblock, fat, file, file_name):
        file_name = bytes(file_name, 'utf-8')
        file_hash = int(hashlib.md5(file_name).hexdigest(), 16) % 1024

        file.seek(superblock.first_cluster_offset + file_hash * 4)
        address = unpack('i', file.read(4))[0]

        clusters = fat.get_clusters_chain(address)
        current_cluster = 0

        file.seek(Root.cluster_offset(superblock, clusters[0]))
        name = ''
        while name != file_name:
            data = unpack('59sci', file.read(64))
            length = ord(data[1])
            name = data[0][:length]

            if file.tell() % superblock.cluster_size == 0 and len(
                    clusters) > current_cluster + 1:
                current_cluster += 1
                file.seek(
                    Root.cluster_offset(superblock, clusters[current_cluster]))

        return Inode.get_inode(superblock.inode_array_offset, file, data[2])

    @staticmethod
    def delete(superblock, fat, file, file_name):
        file_name = bytes(file_name, 'utf-8')
        file_hash = int(hashlib.md5(file_name).hexdigest(), 16) % 1024
        file.seek(superblock.first_cluster_offset + file_hash * 4)
        address = unpack('i', file.read(4))[0]

        clusters = fat.get_clusters_chain(address)
        current_cluster = 0

        file.seek(Root.cluster_offset(superblock, clusters[0]))
        name = ''
        while name != file_name:
            data = unpack('59sci', file.read(64))
            length = ord(data[1])
            name = data[0][:length]

            if file.tell() % superblock.cluster_size == 0 and len(
                    clusters) > current_cluster + 1:
                current_cluster += 1
                file.seek(
                    Root.cluster_offset(superblock, clusters[current_cluster]))

        file.seek(-64, 1)
        file.write(pack('64s', bytes([0] * 64)))

    @staticmethod
    def files_list(superblock, fat, file):
        first_cluster_offset = superblock.first_cluster_offset

        files = {}
        for row in range(1024):
            file.seek(first_cluster_offset + row * 4)
            address = unpack('i', file.read(4))[0]
            if address == -1:
                continue

            clusters = fat.get_clusters_chain(address)
            current_cluster = 0

            file.seek(Root.cluster_offset(superblock, address))
            while True:
                data = unpack('59sci', file.read(64))
                length = ord(data[1])

                if length:
                    position = file.tell()
                    files[data[0][:length].decode()] = Inode.get_inode(
                        superblock.inode_array_offset, file, data[2])
                    file.seek(position)

                if file.tell() % superblock.cluster_size != 0:
                    continue

                if current_cluster + 1 < len(clusters):
                    current_cluster += 1
                    file.seek(Root.cluster_offset(superblock,
                                                  clusters[current_cluster]))
                else:
                    break
        return files

    @staticmethod
    def cluster_offset(superblock, cluster_index):
        return (
            superblock.first_cluster_offset + cluster_index * superblock.cluster_size)

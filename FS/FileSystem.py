from struct import pack, unpack
from time import time
import bcrypt
from FS.SuperBlock import SuperBlock
from FS.FAT import FAT
from FS.InodeMap import InodeMap
from FS.Inode import Inode
from FS.Root import Root
from FS.NoFreeClustersException import NoFreeClustersException


class FileSystem(object):
    def __init__(self, file_name, uid):
        self._file = open(file_name, 'rb+')
        self._superblock = SuperBlock.get_superblock(self._file)
        self._fat = FAT.read(self._superblock.cluster_num,
                             self._superblock.fat_offset, self._file,
                             self._superblock)

        self._inode_map = InodeMap.read(self._superblock.cluster_num,
                                        self._superblock.inode_map_offset,
                                        self._file)
        self._root = Root(self._superblock, self._fat, self._file)
        self._uid = uid

    def __del__(self):
        self._superblock.write(self._file)
        self._fat.write(self._superblock.fat_offset, self._file)
        self._inode_map.write(self._superblock.inode_map_offset, self._file)
        self._file.close()

    def _cluster_offset(self, cluster_index):
        return (
            self._superblock.first_cluster_offset + cluster_index *
            self._superblock.cluster_size)

    def create(self, file_name):
        superblock = self._superblock
        fat = self._fat
        inode_map = self._inode_map
        file = self._file

        if file_name in self._root.list:
            raise FileExistsError()

        if superblock.free_cluster_num == 0:
            raise NoFreeClustersException()

        if len(file_name) > 59:
            raise ValueError()

        inode_id = inode_map.get_free_inode()

        now = int(time())
        inode = Inode(inode_id, uid=self._uid, perm=32, ctime=now, mtime=now)
        try:
            first_cluster = fat.get_free_cluster()
        except NoFreeClustersException:
            raise
        else:
            inode.first_cluster = first_cluster
            Inode.set_inode(superblock.inode_array_offset, file, inode)
            fat.set(index=first_cluster, value=-1)
            inode_map.set(inode.id, False)
            self._root.add(file_name, inode)

    def read(self, file_name):
        if file_name not in self._root.list:
            raise FileNotFoundError()

        superblock = self._superblock
        fat = self._fat
        file = self._file

        inode = self._root.read(file_name)
        perm = inode.perm // 10
        if inode.uid == self._uid and perm < 2:
            raise PermissionError()
        elif inode.uid != self._uid and (perm != 3 and perm != 1):
            raise PermissionError()

        clusters = fat.get_clusters_chain(inode.first_cluster)

        buffer = []
        for cluster_index in clusters:
            file.seek(self._cluster_offset(cluster_index))
            buffer.append(file.read(superblock.cluster_size))

        buffer = b''.join(buffer)[:inode.size]
        return unpack('%ds' % len(buffer), buffer)[0].decode()

    def write(self, file_name, data):
        if file_name not in self._root.list:
            self.create(file_name)

        superblock = self._superblock
        fat = self._fat
        file = self._file
        cluster_offset = self._cluster_offset

        inode = self._root.read(file_name)
        perm = inode.perm % 10
        if inode.uid == self._uid and perm < 2:
            raise PermissionError()
        elif inode.uid != self._uid and (perm != 3 and perm != 1):
            raise PermissionError()

        clusters = self._fat.get_clusters_chain(inode.first_cluster)

        data = bytes(data, 'utf-8')
        data = pack('%ds' % len(data), data)

        len_old_data = inode.size

        cluster_size = superblock.cluster_size

        for index, cluster_index in enumerate(clusters):
            file.seek(cluster_offset(cluster_index))
            file.write(data[index * cluster_size:(index + 1) * cluster_size])

        if len(data) > len_old_data:
            prev_cluster_index = clusters[-1]

            mod = len_old_data % cluster_size
            multiple_len_old_data = len_old_data + cluster_size - mod
            if mod != 0:
                file.seek(cluster_offset(prev_cluster_index) + mod)
                file.write(data[len_old_data:multiple_len_old_data])

            for index in range(multiple_len_old_data, len(data), cluster_size):
                if superblock.free_cluster_num == 0:
                    inode.size = index
                    inode.mtime = int(time())
                    Inode.set_inode(superblock.inode_array_offset, file, inode)
                    self._root.update_inode(file_name, inode)
                    raise NoFreeClustersException()

                cluster_index = fat.get_free_cluster()
                fat.set(index=prev_cluster_index, value=cluster_index)

                file.seek(cluster_offset(cluster_index))
                file.write(data[index:(index + cluster_size)])
                fat.set(index=cluster_index, value=-1)

                prev_cluster_index = cluster_index

            fat.set(index=prev_cluster_index, value=-1)

        inode.size = len(data)
        inode.mtime = int(time())
        Inode.set_inode(superblock.inode_array_offset, file, inode)
        self._root.update_inode(file_name, inode)

    def delete(self, file_name):
        if file_name not in self._root.list:
            raise FileNotFoundError()

        superblock = self._superblock
        fat = self._fat
        file = self._file

        inode = self._root.read(file_name)
        perm = inode.perm % 10
        if inode.uid == self._uid and perm < 2:
            raise PermissionError()
        elif inode.uid != self._uid and (perm != 3 and perm != 1):
            raise PermissionError()

        clusters = fat.get_clusters_chain(inode.first_cluster)

        self._root.delete(file_name)
        Inode.set_inode(superblock.inode_array_offset, file, inode)
        for cluster in clusters:
            fat.set(index=cluster, value=0)

        self._inode_map.set(inode.id, True)

    def rename(self, src, dst):
        files_list = self._root.list

        if src not in files_list:
            raise FileNotFoundError()
        if dst in files_list:
            raise FileExistsError()

        inode = self._root.read(src)
        perm = inode.perm % 10
        if inode.uid == self._uid and perm < 2:
            raise PermissionError()
        elif inode.uid != self._uid and (perm != 3 and perm != 1):
            raise PermissionError()

        self._root.delete(src)
        self._root.add(dst, inode)

    def add_user(self, login, password):
        users = {row.split()[1]: (int(row.split()[0]), row.split()[2]) for row
                 in self.read('users').split('\n')}
        if login in users:
            raise ValueError()

        next_id = max(id for id, hash in users.values()) + 1
        hash = bcrypt.hashpw(password, bcrypt.gensalt())

        users[login] = (next_id, hash)

        data = '\n'.join(
            '{0} {1} {2}'.format(id, login, hash) for login, (id, hash) in
            users.items())
        self.write('users', data)

    def del_user(self, login):
        users = {row.split()[1]: (int(row.split()[0]), row.split()[2]) for row
                 in self.read('users').split('\n')}
        if login not in users:
            raise ValueError

        del (users[login])

        data = '\n'.join(
            '{0} {1} {2}'.format(id, login, hash) for login, (id, hash) in
            users.items())
        self.write('users', data)

    @staticmethod
    def format(file_name, password='admin', size=50 * 1024 * 1024):
        file = open(file_name, 'wb')

        file.seek(size - 1)
        file.write(b'\0')

        superblock = SuperBlock.default(size)
        fat = FAT.empty(superblock.cluster_num, superblock)

        inode_map = InodeMap.empty(superblock.cluster_num)

        file.seek(superblock.inode_array_offset)
        inode_table = [Inode(id) for id in range(superblock.cluster_num)]
        for inode in inode_table:
            file.write(inode.pack())

        cluster_size = superblock.cluster_size
        offset = cluster_size - file.tell() % cluster_size
        superblock.first_cluster_offset = file.tell() + offset
        superblock.free_cluster_num = (
            superblock.cluster_num - superblock.first_cluster_offset //
            cluster_size)

        Root.write(superblock, fat, inode_map, inode_table[0], file)

        superblock.write(file)
        fat.write(superblock.fat_offset, file)
        inode_map.write(superblock.inode_map_offset, file)

        file.close()

        fs = FileSystem(file_name, 0)
        fs.create('users')
        fs.write('users',
                 '0 admin %s' % bcrypt.hashpw(password, bcrypt.gensalt()))

    @property
    def files_list(self):
        return self._root.list

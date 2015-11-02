from struct import pack, unpack
from time import time

import bcrypt
from FS.SuperBlock import SuperBlock
from FS.FAT import FAT
from FS.InodeBitmap import InodeBitmap
from FS.Inode import Inode
from FS.Root import Root


class FileSystem(object):
    def __init__(self, file_name, uid):
        self.file = open(file_name, 'rb+')
        self.superblock = SuperBlock.get_superblock(self.file)
        self.fat = FAT.get_fat(self.superblock.cluster_num,
                               self.superblock.fat_offset, self.file)
        self.inode_bitmap = InodeBitmap.get_bitmap(self.superblock.cluster_num,
                                                   self.superblock.inode_bitmap_offset,
                                                   self.file)
        self.uid = uid
        self.files_list = Root.files_list(self.superblock, self.fat, self.file)

    def __del__(self):
        self.superblock.write(self.file)
        self.fat.write(self.superblock.fat_offset, self.file)
        self.inode_bitmap.write(self.superblock.inode_bitmap_offset, self.file)
        self.file.close()

    def cluster_offset(self, cluster_index):
        return (
            self.superblock.first_cluster_offset + cluster_index *
            self.superblock.cluster_size)

    @staticmethod
    def format(file_name, password='admin', size=50 * 1024 * 1024):
        file = open(file_name, 'wb')

        file.seek(size - 1)
        file.write(b'\0')

        superblock = SuperBlock.default(size)
        fat = FAT.empty(superblock.cluster_num)

        inode_bitmap = InodeBitmap.empty(superblock.cluster_num)

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

        root = Root()
        root.write(superblock, fat, inode_bitmap, inode_table[0], file)

        superblock.write(file)
        fat.write(superblock.fat_offset, file)
        inode_bitmap.write(superblock.inode_bitmap_offset, file)

        file.close()

        fs = FileSystem(file_name, 0)
        fs.create('users')
        fs.write('users',
                 '0 admin %s' % bcrypt.hashpw(password, bcrypt.gensalt()))

    def create(self, file_name):
        superblock = self.superblock
        fat = self.fat
        inode_bitmap = self.inode_bitmap
        file = self.file

        if file_name in self.files_list:
            raise FileExistsError('Файл с данным именем уже существует')

        if superblock.free_cluster_num == 0:
            raise NoFreeClustersException(
                'Не осталось свободных блоков данных')

        if len(file_name) > 59:
            raise ValueError('Длина файла должна быть не более 59')

        inode_array_offset = superblock.inode_array_offset
        inode_id = inode_bitmap.list.index(True)

        Root.add(superblock, fat, file, file_name, inode_id)

        inode = Inode(inode_id)
        inode.uid = self.uid
        inode.perm = 32
        inode.ctime = inode.mtime = int(time())
        first_cluster = fat.list.index(0)
        inode.first_cluster = first_cluster
        Inode.set_inode(inode_array_offset, file, inode_id, inode)
        fat.set_el(superblock, first_cluster, -1)
        inode_bitmap.list[inode.id] = False
        self.files_list[file_name] = inode

    def read(self, file_name):
        if file_name not in self.files_list:
            raise FileNotFoundError('Файл с таким именем отсутствует')

        superblock = self.superblock
        fat = self.fat
        file = self.file
        inode = Root.read(superblock, fat, file, file_name)

        perm = inode.perm // 10
        if inode.uid == self.uid and perm < 2:
            raise PermissionError('Нет прав на чтение')
        elif inode.uid != self.uid and (perm != 3 and perm != 1):
            raise PermissionError('Нет прав на чтение')

        first_cluster = inode.first_cluster
        clusters = [first_cluster]

        next = fat.list[first_cluster]
        while next != -1:
            clusters.append(next)
            next = fat.list[next]

        buffer = []
        for cluster_index in clusters:
            file.seek(self.cluster_offset(cluster_index))
            buffer.append(file.read(superblock.cluster_size))

        buffer = b''.join(buffer)[:inode.size]
        return unpack('%ds' % len(buffer), buffer)[0].decode()

    def write(self, file_name, data):
        if file_name not in self.files_list:
            self.create(file_name)

        superblock = self.superblock
        fat = self.fat
        file = self.file
        cluster_offset = self.cluster_offset

        inode = Root.read(superblock, fat, file, file_name)

        perm = inode.perm % 10
        if inode.uid == self.uid and perm < 2:
            raise PermissionError('Нет прав на запись')
        elif inode.uid != self.uid and (perm != 3 and perm != 1):
            raise PermissionError('Нет прав на запись')

        first_cluster = inode.first_cluster
        clusters = [first_cluster]

        next = fat.list[first_cluster]
        while next != -1:
            clusters.append(next)
            next = fat.list[next]

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
                    Inode.set_inode(superblock.inode_array_offset, file,
                                    inode.id, inode)
                    self.files_list[file_name] = inode
                    raise NoFreeClustersException(
                        'Не осталось свободных блоков данных')

                cluster_index = fat.list.index(0)
                fat.set_el(superblock, prev_cluster_index, cluster_index)

                file.seek(cluster_offset(cluster_index))
                file.write(data[index:(index + cluster_size)])
                fat.set_el(superblock, cluster_index, -1)
                prev_cluster_index = cluster_index
            fat.set_el(superblock, prev_cluster_index, -1)

        inode.size = len(data)
        inode.mtime = int(time())
        Inode.set_inode(superblock.inode_array_offset, file, inode.id, inode)
        self.files_list[file_name] = inode

    def delete(self, file_name):
        if file_name not in self.files_list:
            raise FileNotFoundError('Файл с таким именем отсутствует')

        superblock = self.superblock
        fat = self.fat
        file = self.file

        inode = Root.read(self.superblock, self.fat, self.file, file_name)

        perm = inode.perm % 10
        if inode.uid == self.uid and perm < 2:
            raise PermissionError('Нет прав на удаление')
        elif inode.uid != self.uid and (perm != 3 and perm != 1):
            raise PermissionError('Нет прав на удаление')

        first_cluster = inode.first_cluster
        clusters = [first_cluster]
        next = fat.list[first_cluster]
        while next != -1:
            clusters.append(next)
            next = fat.list[next]

        Root.delete(superblock, fat, file, file_name)
        Inode.set_inode(superblock.inode_array_offset, file, inode.id, inode)
        for cluster in clusters:
            fat.set_el(superblock, cluster, 0)

        self.inode_bitmap.list[inode.id] = True
        del (self.files_list[file_name])

    def add_user(self, login, password):
        users = {row.split()[1]: (int(row.split()[0]), row.split()[2]) for row
                 in self.read('users').split('\n')}
        if login in users:
            raise ValueError('Пользователь с данным логином уже существует')

        next_id = max(id for id, hash in users.values()) + 1
        hash = bcrypt.hashpw(password, bcrypt.gensalt())

        users[login] = (next_id, hash)

        data = '\n'.join(
            '{0} {1} {2}'.format(id, login, hash) for login, (id, hash) in
            users.items())
        self.write('users', data)


class NoFreeClustersException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)

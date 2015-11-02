from struct import pack, unpack, calcsize


class Inode(object):
    format = '7i'
    size = calcsize(format)

    def __init__(self, id, uid=0, perm=0, size=0, ctime=0, mtime=0,
                 first_cluster=-1):
        self.id = id
        self.uid = uid
        self.perm = perm
        self.size = size
        self.ctime = ctime
        self.mtime = mtime
        self.first_cluster = first_cluster

    def pack(self):
        return pack(self.format, self.id, self.uid, self.perm, self.size,
                    self.ctime, self.mtime, self.first_cluster)

    @staticmethod
    def get_inode(inode_array_offset, file, index):
        file.seek(inode_array_offset + Inode.size * index)
        return Inode(*unpack(Inode.format, file.read(Inode.size)))

    @staticmethod
    def set_inode(inode_array_offset, file, index, inode):
        file.seek(inode_array_offset + Inode.size * index)
        file.write(inode.pack())

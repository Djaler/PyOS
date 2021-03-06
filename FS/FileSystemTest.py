import unittest
from FS.FileSystem import FileSystem


class MyTestCase(unittest.TestCase):
    def test_read_and_write_small(self):
        FileSystem.format('test')
        fs = FileSystem('test')

        text = '1'
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

    def test_append_write(self):
        FileSystem.format('test')
        fs = FileSystem('test')

        text = ''.join(str(i) for i in range(10000))
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

        append_text = ''.join(str(i) for i in reversed(range(10000)))
        fs.append('file1', append_text)

        res = fs.read('file1')
        self.assertEqual(text + append_text, res)

    def test_set_permissions(self):
        FileSystem.format('test')
        fs = FileSystem('test')

        fs.create('file')
        self.assertTrue(fs.files_list['file'].owner_read)
        self.assertTrue(fs.files_list['file'].owner_write)
        self.assertTrue(fs.files_list['file'].other_read)
        self.assertFalse(fs.files_list['file'].other_write)

        fs.set_permissions('file', True, True, False, False)
        self.assertTrue(fs.files_list['file'].owner_read)
        self.assertTrue(fs.files_list['file'].owner_write)
        self.assertFalse(fs.files_list['file'].other_read)
        self.assertFalse(fs.files_list['file'].other_write)

    def test_read_and_write(self):
        FileSystem.format('test')
        fs = FileSystem('test')

        text = ''.join(str(i) for i in range(1000))
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

        text = ''.join(str(i) for i in range(100000))
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

        text = ''.join(str(i) for i in range(1000000))
        fs.write('file2', text)

        res = fs.read('file2')
        self.assertEqual(text, res)

        with self.assertRaises(FileNotFoundError):
            fs.read('file3')

    def test_create_and_delete(self):
        FileSystem.format('test')
        fs = FileSystem('test')
        self.assertEqual(sorted(fs.files_list.keys()), ['users'])

        fs.create('file1')
        self.assertEqual(sorted(fs.files_list.keys()),
                         sorted(['users', 'file1']))

        fs.create('file2')
        self.assertEqual(sorted(fs.files_list.keys()),
                         sorted(['users', 'file1', 'file2']))

        fs.delete('file2')
        self.assertEqual(sorted(fs.files_list.keys()),
                         sorted(['users', 'file1']))

        with self.assertRaises(FileExistsError):
            fs.create('file1')

        with self.assertRaises(ValueError):
            long_name = ''.join(['0'] * 60)
            fs.create(long_name)

    def test_rename(self):
        FileSystem.format('test')
        fs = FileSystem('test')
        self.assertEqual(sorted(fs.files_list.keys()), ['users'])

        fs.create('file1')
        self.assertEqual(sorted(fs.files_list.keys()),
                         sorted(['users', 'file1']))

        fs.rename('file1', 'file2')
        self.assertEqual(sorted(fs.files_list.keys()),
                         sorted(['users', 'file2']))

        fs.create('file3')
        self.assertEqual(sorted(fs.files_list.keys()),
                         sorted(['users', 'file2', 'file3']))

        with self.assertRaises(FileExistsError):
            fs.rename('file3', 'file2')

    def test_hash_table(self):
        FileSystem.format('test')
        fs = FileSystem('test')

        for i in range(1000):
            fs.write(str(i), str(i))
        for i in range(1000):
            self.assertEqual(fs.read(str(i)), str(i))

    def test_users(self):
        FileSystem.format('test')
        fs = FileSystem('test')
        self.assertIn('admin', fs.read('users'))

        fs.add_user('user1', 'password')
        self.assertIn('user1', fs.read('users'))

        fs.del_user('user1')
        self.assertNotIn('user1', fs.read('users'))

        with self.assertRaises(ValueError):
            fs.del_user('user1')

        with self.assertRaises(ValueError):
            fs.add_user('admin', 'password')


if __name__ == '__main__':
    unittest.main()

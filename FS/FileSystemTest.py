import unittest

from FS.FileSystem import FileSystem


class MyTestCase(unittest.TestCase):
    def test_read_and_write_small(self):
        FileSystem.format('test')
        fs = FileSystem('test', 1)

        fs.create('file1')
        text = '1'
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

    def test_read_and_write(self):
        FileSystem.format('test')
        fs = FileSystem('test', 1)

        fs.create('file1')
        text = ''.join(str(i) for i in range(1000))
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

        text = ''.join(str(i) for i in range(100000))
        fs.write('file1', text)

        res = fs.read('file1')
        self.assertEqual(text, res)

        fs.create('file2')
        text = ''.join(str(i) for i in range(1000000))
        fs.write('file2', text)

        res = fs.read('file2')
        self.assertEqual(text, res)

        with self.assertRaises(FileNotFoundError):
            fs.read('file3')

    def test_create_and_delete(self):
        FileSystem.format('test')
        fs = FileSystem('test', 0)

        self.assertEqual(sorted(fs._files_list.keys()), ['users'])

        fs.create('file1')

        self.assertEqual(sorted(fs._files_list.keys()),
                         sorted(['users', 'file1']))

        fs.create('file2')

        self.assertEqual(sorted(fs._files_list.keys()),
                         sorted(['users', 'file1', 'file2']))

        fs.delete('file2')

        self.assertEqual(sorted(fs._files_list.keys()),
                         sorted(['users', 'file1']))

    def test_hash_table(self):
        FileSystem.format('test')
        fs = FileSystem('test', 1)

        for i in range(10000):
            fs.create(str(i))
        for i in range(10000):
            fs.write(str(i), str(i))
        for i in range(10000):
            self.assertEqual(fs.read(str(i)), str(i))


if __name__ == '__main__':
    unittest.main()

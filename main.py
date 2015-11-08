import os
import subprocess
import bcrypt
from getpass import getpass
from pyfiglet import figlet_format
from FS.FileSystem import FileSystem
from FS.FileSystem import NoFreeClustersException

os.system('clear')

if not os.path.exists('file'):
    print('Происходит создание файловой системы.')
    password = ''
    while not password:
        password = getpass('Введите желаемый пароль admin: ')

    FileSystem.format('file', password, size=100 * 1024 * 1024)

    input()
    os.system('clear')

users = FileSystem('file', 0).users

login = ''
while login not in users:
    login = input('login:')
hashed = users[login][1]
hash = ''
while hash is hashed:
    hash = bcrypt.hashpw(getpass('password:'), hashed)

os.system('clear')
print(figlet_format('WELCOME HOME,  MR. %s' % login.upper(), font='big',
                    width=int(
                        subprocess.check_output(['stty', 'size']).split()[1])))

fs = FileSystem('file', users[login][0])

# TODO изменение атрибутов

while True:
    command = input('>')

    if command.startswith('create'):
        file_name = command.split()[1]
        try:
            fs.create(file_name)
        except (FileExistsError, NoFreeClustersException, ValueError) as e:
            print(e)

    if command.startswith('read'):
        file_name = command.split()[1]
        try:
            print(fs.read(file_name))
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    if command.startswith('write'):
        file_name = command.split()[1]
        data = command[len('write ' + file_name) + 1:]
        try:
            fs.write(file_name, data)
        except (PermissionError, NoFreeClustersException) as e:
            print(e)

    if command.startswith('delete'):
        file_name = command.split()[1]
        try:
            fs.delete(file_name)
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    if command.startswith('rename'):
        src = command.split()[1]
        dst = command.split()[2]
        try:
            fs.rename(src, dst)
        except (FileNotFoundError, PermissionError, FileExistsError) as e:
            print(e)

    if command.startswith('list'):
        files_list = fs.files_list
        for file_name in sorted(files_list):
            inode = files_list[file_name]
            size = inode.size
            if 1024 <= size < 1024 ** 2:
                size = str(size // 1024) + 'K'
            elif 1024 ** 2 <= size < 1024 ** 3:
                size = str(size // (1024 ** 2)) + 'M'
                print(file_name, size)

    if command.startswith('add_user'):
        login = command.split()[1]
        password = getpass('Пароль: ')
        try:
            fs.add_user(login, password)
        except (ValueError, PermissionError) as e:
            print(e)

    if command.startswith('del_user'):
        login = command.split()[1]
        try:
            fs.del_user(login)
        except (ValueError, PermissionError) as e:
            print(e)

    if command.startswith('exit'):
        exit()

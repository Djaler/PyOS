import os
import subprocess
from getpass import getpass
import bcrypt
from pyfiglet import figlet_format
from prettytable import PrettyTable
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from FS.FileSystem import FileSystem, NoFreeClustersException


class PyOS(object):
    def __init__(self, file_name):
        self._cls()
        if not os.path.exists(file_name):
            self._format_file(file_name)

        users = FileSystem('file', 0).users

        self._uid, login = self._login(users)

        self._fs = FileSystem('file', users[login][0])

        self._cls()
        width_window = int(
            subprocess.check_output(['stty', 'size']).split()[1])
        print(
            figlet_format('WELCOME HOME,  MR. %s' % login.upper(), font='big',
                          width=width_window))

    def run(self):
        history = InMemoryHistory()

        while True:
            command = prompt('>', auto_suggest=AutoSuggestFromHistory(),
                             history=history)

            if command.startswith('create'):
                self._create(command)
            elif command.startswith('read'):
                self._read(command)
            elif command.startswith('write'):
                self._write(command)
            elif command.startswith('append'):
                self._append(command)
            elif command.startswith('rename'):
                self._rename(command)
            elif command.startswith('delete'):
                self._delete(command)
            elif command.startswith('set_perm'):
                self._set_perm(command)
            elif command.startswith('list'):
                self._list(command)
            elif command.startswith('add_user'):
                self._add_user(command)
            elif command.startswith('del_user'):
                self._del_user(command)
            elif command.startswith('exit'):
                exit()

    def _create(self, command):
        file_name = command.split()[1]
        try:
            self._fs.create(file_name)
        except (FileExistsError, NoFreeClustersException, ValueError) as e:
            print(e)

    def _read(self, command):
        file_name = command.split()[1]
        try:
            print(self._fs.read(file_name))
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    def _write(self, command):
        file_name = command.split()[1]
        data = prompt('Введите текст:\n', multiline=True)
        try:
            self._fs.write(file_name, data)
        except (PermissionError, NoFreeClustersException) as e:
            print(e)

    def _append(self, command):
        file_name = command.split()[1]
        data = prompt('Введите текст:\n', multiline=True)
        try:
            self._fs.append(file_name, data)
        except (PermissionError, NoFreeClustersException) as e:
            print(e)

    def _rename(self, command):
        src = command.split()[1]
        dst = command.split()[2]
        try:
            self._fs.rename(src, dst)
        except (FileNotFoundError, PermissionError, FileExistsError) as e:
            print(e)

    def _delete(self, command):
        file_name = command.split()[1]
        try:
            self._fs.delete(file_name)
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    def _set_perm(self, command):
        file_name = command.split()[1]
        perm = command.split()[2]
        try:
            permissions = (
                perm[0] == 'r', perm[1] == 'w', perm[2] == 'r', perm[3] == 'w')
            self._fs.set_permissions(file_name, *permissions)
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    def _list(self, command):
        files_list = self._fs.files_list
        users = {id: login for login, (id, hash) in self._fs.users.items()}
        table = PrettyTable(
            ['Название', 'Размер', 'Права доступа', 'Владелец'])
        table.border = False

        for file_name in sorted(files_list):
            inode = files_list[file_name]

            size = inode.size
            if 1024 <= size < 1024 ** 2:
                size = str(size // 1024) + 'K'
            elif 1024 ** 2 <= size < 1024 ** 3:
                size = str(size // (1024 ** 2)) + 'M'

            permissions = ['r' if inode.owner_read else '-',
                           'w' if inode.owner_write else '-',
                           'r' if inode.other_read else '-',
                           'w' if inode.other_write else '-']
            table.add_row(
                [file_name, size, ''.join(permissions), users[inode.uid]])
        print(table)

    def _add_user(self, command):
        login = command.split()[1]
        password = getpass('Пароль:')
        try:
            self._fs.add_user(login, password)
        except (ValueError, PermissionError) as e:
            print(e)

    def _del_user(self, command):
        login = command.split()[1]
        try:
            self._fs.del_user(login)
        except (ValueError, PermissionError) as e:
            print(e)

    @staticmethod
    def _login(users):
        login = input('login:')
        while login not in users:
            print('Неверное имя пользователя')
            login = input('login:')
        hashed = users[login][1]
        hash = bcrypt.hashpw(getpass('password:'), hashed)
        while hash != hashed:
            print('Неверный пароль')
            hash = bcrypt.hashpw(getpass('password:'), hashed)
        return users[login][0], login

    @staticmethod
    def _format_file(file_name):
        print('Происходит создание файловой системы.')
        password = ''
        while not password:
            password = getpass('Введите желаемый пароль admin: ')

        FileSystem.format(file_name, password, size=50 * 1024 * 1024)

    @staticmethod
    def _cls():
        os.system('clear')


if __name__ == '__main__':
    PyOS('file').run()

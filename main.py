import os
import subprocess
from getpass import getpass
from time import sleep
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

        self._fs = FileSystem(file_name)
        self._file_name = file_name

        self._init_commands()

    def run(self):
        self._login(self._fs.users)

        history = InMemoryHistory()

        while True:
            command = prompt('>', auto_suggest=AutoSuggestFromHistory(),
                             history=history).split()
            if command:
                try:
                    self._commands[command[0]](command)
                except KeyError:
                    self._command_not_found()

    def _init_commands(self):
        methods = [self._create, self._read, self._write, self._append,
                   self._copy, self._rename, self._delete, self._set_perm,
                   self._list, self._add_user, self._del_user, self._exit,
                   self._help]
        self._commands = {method.__name__[1:]: method for method in methods}

    def _create(self, command):
        """Создать файл"""
        if len(command) != 2:
            self._command_not_found()
            return

        try:
            self._fs.create(command[1])
        except (FileExistsError, NoFreeClustersException, ValueError) as e:
            print(e)

    def _read(self, command):
        """Читать из файла"""
        if len(command) != 2:
            self._command_not_found()
            return

        try:
            print(self._fs.read(command[1]))
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    def _write(self, command):
        """Записать в файл"""
        if len(command) != 2:
            self._command_not_found()
            return

        data = prompt('Введите текст:\n', multiline=True)
        try:
            self._fs.write(command[1], data)
        except (PermissionError, NoFreeClustersException) as e:
            print(e)

    def _append(self, command):
        """Дописать в файл"""
        if len(command) != 2:
            self._command_not_found()
            return

        data = prompt('Введите текст:\n', multiline=True)
        try:
            self._fs.append(command[1], data)
        except (PermissionError, NoFreeClustersException) as e:
            print(e)

    def _copy(self, command):
        """Скопировить файл"""
        if len(command) != 3:
            self._command_not_found()
            return

        try:
            self._fs.copy(command[1], command[2])
        except (FileNotFoundError, PermissionError, FileExistsError,
                NoFreeClustersException) as e:
            print(e)

    def _rename(self, command):
        """Переименовать файл"""
        if len(command) != 3:
            self._command_not_found()
            return

        try:
            self._fs.rename(command[1], command[2])
        except (FileNotFoundError, PermissionError, FileExistsError) as e:
            print(e)

    def _delete(self, command):
        """Удалить файл"""
        if len(command) != 2:
            self._command_not_found()
            return

        try:
            self._fs.delete(command[1])
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    def _set_perm(self, command):
        """Установить права доступа"""
        if len(command) != 3:
            self._command_not_found()
            return

        perm = command[2]
        try:
            permissions = (
                perm[0] == 'r', perm[1] == 'w', perm[2] == 'r', perm[3] == 'w')
            self._fs.set_permissions(command[1], *permissions)
        except (FileNotFoundError, PermissionError) as e:
            print(e)

    def _list(self, command):
        """Список файлов"""
        if len(command) != 1:
            self._command_not_found()
            return

        files_list = self._fs.files_list
        users = {id: login for login, (id, hash) in self._fs.users.items()}
        table = PrettyTable(
            ['Название', 'Размер', 'Права доступа', 'Владелец'], border=0,
            padding_width=2)

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
        """Добавить пользователя"""
        if len(command) != 2:
            self._command_not_found()
            return

        password = getpass('Пароль:')
        try:
            self._fs.add_user(command[1], password)
        except (ValueError, PermissionError) as e:
            print(e)

    def _del_user(self, command):
        """Удалить пользователя"""
        if len(command) != 2:
            self._command_not_found()
            return

        try:
            self._fs.del_user(command[1])
        except (ValueError, PermissionError) as e:
            print(e)

    def _exit(self, command):
        """Выйти из системы"""
        if len(command) != 1:
            self._command_not_found()
            return

        exit()

    def _help(self, command):
        """Отобразить справку"""
        if len(command) != 1:
            self._command_not_found()
            return

        for name, command in sorted(self._commands.items()):
            print('{0} - {1}'.format(name, command.__doc__))

    def _login(self, users):
        login = input('login:')
        while login not in users:
            print('Неверное имя пользователя')
            login = input('login:')

        hashed = users[login][1]
        hash = bcrypt.hashpw(getpass('password:'), hashed)
        while hash != hashed:
            print('Неверный пароль')
            hash = bcrypt.hashpw(getpass('password:'), hashed)
        self._cls()
        uid = users[login][0]

        if login.lower() == 'neo':
            from matrix_curses import matrix_curses

            matrix_curses.run(3)

        if uid != 0:
            del self._fs
            self._fs = FileSystem(self._file_name, uid)

        if login.lower() != 'neo':
            width_window = int(
                subprocess.check_output(['stty', 'size']).split()[1])
            print(figlet_format('WELCOME HOME,  MR. %s' % login.upper(),
                                font='big', width=width_window))
        else:
            from sys import stdout
            from random import randint
            from colorama import init, Fore

            init()
            print(Fore.GREEN, end='')
            stdout.flush()

            string = 'Wake up, Neo...'

            for char in string:
                print(char, end='')
                stdout.flush()
                sleep(randint(10, 40) / 100)
            print()

    @staticmethod
    def _command_not_found():
        print('Команда не распознана')

    @staticmethod
    def _cls():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def _format_file(file_name):
        print('Происходит создание файловой системы.')
        password = ''
        while not password:
            password = getpass('Введите желаемый пароль admin: ')

        FileSystem.format(file_name, password, size=50 * 1024 * 1024)


if __name__ == '__main__':
    PyOS('file').run()

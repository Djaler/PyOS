import os
import subprocess
import bcrypt
from pyfiglet import figlet_format
from FS.FileSystem import FileSystem
from FS.NoFreeClustersException import NoFreeClustersException

os.system('clear')

if not os.path.exists('file'):
    print('Происходит создание файловой системы.')
    password = ''
    while not password:
        password = input('Введите желаемый пароль admin: ')
    FileSystem.format('file', password)
    os.system('clear')

fs = FileSystem('file', 0)

users = {row.split()[1]: (int(row.split()[0]), row.split()[2]) for row in
         fs.read('users').split('\n')}
del fs

login = ''
while login not in users:
    login = input('login:')
hashed = users[login][1]
hash = ''
while hash != hashed:
    hash = bcrypt.hashpw(input('password:'), hashed)

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
        except FileExistsError:
            print('Файл с данным именем уже существует')
        except NoFreeClustersException:
            print('Не осталось свободных блоков данных')
        except ValueError:
            print('Имя файла должно быть не более 59 символов')
        except Exception as e:
            print(str(e))

    if command.startswith('read'):
        file_name = command.split()[1]
        try:
            print(fs.read(file_name))
        except FileNotFoundError:
            print('Файл с таким именем отсутствует')
        except PermissionError:
            print('Нет прав')
        except Exception as e:
            print(str(e))

    if command.startswith('write'):
        file_name = command.split()[1]
        data = command[len('write ' + file_name) + 1:]
        try:
            fs.write(file_name, data)
        except PermissionError:
            print('Нет прав')
        except NoFreeClustersException:
            print('Не осталось свободных блоков данных')
        except Exception as e:
            print(str(e))

    if command.startswith('delete'):
        file_name = command.split()[1]
        try:
            fs.delete(file_name)
        except FileNotFoundError:
            print('Файл с таким именем отсутствует')
        except PermissionError:
            print('Нет прав')
        except Exception as e:
            print(str(e))

    if command.startswith('rename'):
        src = command.split()[1]
        dst = command.split()[2]
        try:
            fs.rename(src, dst)
        except FileNotFoundError:
            print('Файл с таким именем отсутствует')
        except PermissionError:
            print('Нет прав')
        except FileExistsError:
            print('Файл с данным именем уже существует')
        except Exception as e:
            print(str(e))

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
        password = command.split()[2]
        try:
            fs.add_user(login, password)
        except ValueError:
            print('Такой пользователь уже существует')
        except PermissionError:
            print('Нет прав')
        except Exception as e:
            print(str(e))

    if command.startswith('del_user'):
        login = command.split()[1]
        try:
            fs.del_user(login)
        except ValueError:
            print('Такого пользователя нет')
        except PermissionError:
            print('Нет прав')
        except Exception as e:
            print(str(e))

    if command.startswith('exit'):
        exit()

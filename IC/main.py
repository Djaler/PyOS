from threading import Thread, current_thread
from time import sleep

from IC.semaphore import Semaphore
from IC.shared_memory import SharedMemory


def producer(count, empty, full, mutex, key, memory):
    current_thread_name = current_thread().name
    shared_memory = memory.get_page(key)
    while not shared_memory:
        print(current_thread_name, 'ожидает освобождения страницы памяти')
        sleep(1)
        shared_memory = memory.get_page(key)

    for item in range(count):
        print(current_thread_name, 'произвел элемент', item)
        while not empty.down():
            print(current_thread_name, 'ожидает появления места для элемента')
            sleep(1)

        while not mutex.down():
            print(current_thread_name, 'ожидает входа в критическую область')
            sleep(1)

        print(current_thread_name, 'вошел в критическую область')
        shared_memory.append(str(item))
        print(current_thread_name, 'поместил элемент', item, 'в буфер')
        print(current_thread_name, 'вышел из критической области')
        mutex.up()
        full.up()
    print(current_thread_name, 'завершил работу')


def consumer(count, empty, full, mutex, key, memory):
    current_thread_name = current_thread().name
    shared_memory = memory.get_page(key)
    while not shared_memory:
        print(current_thread_name, 'ожидает освобождения страницы памяти')
        sleep(1)
        shared_memory = memory.get_page(key)

    for _ in range(count):
        while not full.down():
            print(current_thread_name, 'ожидает новый элемент')
            sleep(1)

        while not mutex.down():
            print(current_thread_name, 'ожидает входа в критическую область')
            sleep(1)

        print(current_thread_name, 'вошел в критическую область')
        print(current_thread_name, 'считал элемент', shared_memory.pop(),
              'из буфера')
        print(current_thread_name, 'вышел из критической области')
        mutex.up()
        empty.up()
    print(current_thread_name, 'завершил работу')
    memory.clear_page(key)


page_size = 3
page_count = 1

memory = SharedMemory(page_size=page_size, page_count=page_count)

mutex = Semaphore(max=1, value=1)


def create_pair(page_size, memory, mutex, key, count):
    empty = Semaphore(max=page_size, value=page_size)
    full = Semaphore(max=page_size, value=0)
    producer_thread = Thread(target=producer,
                             args=(count, empty, full, mutex, key, memory),
                             name='Producer_%d' % key)
    consumer_thread = Thread(target=consumer,
                             args=(count, empty, full, mutex, key, memory),
                             name='Consumer_%d' % key)

    return producer_thread, consumer_thread


producer_1, consumer_1 = create_pair(page_size, memory, mutex, key=1, count=5)
producer_2, consumer_2 = create_pair(page_size, memory, mutex, key=2, count=4)

producer_1.start()
producer_2.start()
consumer_1.start()
consumer_2.start()

producer_1.join()
producer_2.join()
consumer_1.join()
consumer_2.join()

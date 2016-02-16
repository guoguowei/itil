# coding=utf8
'''
用sysv_ipc来存储计数值

内存存储的格式

    4字节长度标记 8字节itil_id_key 8字节itil_id_key对应的value 8字节itil_id_key 8字节itil_id_key对应的value ......

    4字节长度标记表示后面的内存块,需要读取多少个字节
'''
__author__ = 'guozhiwei'

try:
    import sysv_ipc
except:
    pass
import struct
import time
import logging
import traceback

LONG_LONG_SIZE = 8
UNSIGN_INT_SIZE = 4

SEMAPHORE_KEY = 1026
SHARED_MEMORY_KEY = 1026

GLOBAL_SEMAPHORE = None
GLOBAL_SHARE_MEMORY = None


def get_semaphore():
    global GLOBAL_SEMAPHORE
    if GLOBAL_SEMAPHORE:
        return GLOBAL_SEMAPHORE
    try:
        semaphore = sysv_ipc.Semaphore(
            SEMAPHORE_KEY, sysv_ipc.IPC_CREX, mode=0666)
    except sysv_ipc.ExistentialError:
        semaphore = sysv_ipc.Semaphore(SEMAPHORE_KEY)
        while not semaphore.o_time:
            time.sleep(.1)
    else:
        semaphore.release()
    GLOBAL_SEMAPHORE = semaphore
    return GLOBAL_SEMAPHORE


def get_sysv_memory():
    global GLOBAL_SHARE_MEMORY
    if GLOBAL_SHARE_MEMORY:
        return GLOBAL_SHARE_MEMORY
    try:
        memory = sysv_ipc.SharedMemory(
            SHARED_MEMORY_KEY, sysv_ipc.IPC_CREX, mode=0666)
    except sysv_ipc.ExistentialError:
        memory = sysv_ipc.SharedMemory(SHARED_MEMORY_KEY)
    GLOBAL_SHARE_MEMORY = memory
    return GLOBAL_SHARE_MEMORY


def incr(itil_id, incr_value=1):
    try:
        _set(itil_id, types=1, incr_value=incr_value)
    except:
        logging.error(traceback.format_exc())


def _set(itil_id, types=1, incr_value=1, value=None):
    '''

    :param itil_id: int
    :param types:   1表示递增    2表示设置值
    :param incr_value:
    :param value:
    :return:
    '''
    if type(itil_id) != int:
        return
    sem = get_semaphore()
    memory = get_sysv_memory()
    try:
        # 最多等待锁0.X秒
        sem.acquire(0.05)
        read_first_int_bit = memory.read(UNSIGN_INT_SIZE)
        read_first_int = struct.unpack('!I', read_first_int_bit)
        read_first_int = read_first_int[0]

        if read_first_int == 0x20202020 or read_first_int == 0:
            # 还没有存储数据
            if types == 1:
                init_value = 1
            elif types == 2:
                init_value = value
            ready_write_data = struct.pack(
                "!IQQ", LONG_LONG_SIZE * 2, itil_id, init_value)

            memory.write(ready_write_data)
        else:
            # 多少个unsigned long long
            num_Q = read_first_int / LONG_LONG_SIZE
            num_not_read_Q = num_Q

            loop_time = 0
            is_find_key = False
            while num_not_read_Q > 0:
                data = memory.read(16, 4 + loop_time * 16)
                num_not_read_Q = num_not_read_Q - 2
                key_value = struct.unpack("!QQ", data)
                itil_key = key_value[0]
                itil_value = key_value[1]
                loop_time += 1
                # logging.debug("keyvalue %s key %s id %s",key_value,itil_key, itil_id)
                if itil_key == itil_id:
                    if types == 1:
                        itil_value += incr_value
                    elif types == 2:
                        itil_value = value
                    itil_value_bit = struct.pack("!Q", itil_value)
                    offset = (
                        UNSIGN_INT_SIZE + (num_Q - num_not_read_Q) * LONG_LONG_SIZE - LONG_LONG_SIZE)
                    memory.write(itil_value_bit, offset)
                    is_find_key = True
                    break
            if not is_find_key:
                # logging.debug("key %s id %s",itil_key, itil_id)
                if types == 1:
                    tmp_value = 1
                elif types == 2:
                    tmp_value = value
                itil_value_bit = struct.pack("!QQ", itil_id, tmp_value)
                offset = UNSIGN_INT_SIZE + num_Q * LONG_LONG_SIZE
                read_first_int_bit = struct.pack(
                    "!I", read_first_int + LONG_LONG_SIZE * 2)
                memory.write(read_first_int_bit)
                memory.write(itil_value_bit, offset)

        sem.release()

    except sysv_ipc.BusyError:
        logging.warning("BusyError itil id %s", itil_id)

    except:
        sem.release()
        logging.error(traceback.format_exc())


def set(itil_id, value):
    try:
        _set(itil_id, types=2, value=value)
    except:
        logging.error(traceback.format_exc())


if __name__ == '__main__':
    for i in range(1):
        # incr(0x1000000000,1)
        # incr(0x1000000001,3)
        # incr(0x1000000002,99)
        set(0x1000000002, 1000023232)

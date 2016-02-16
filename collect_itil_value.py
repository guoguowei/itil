#coding=utf8
'''
上报sysv 共享内存中存储的计数值
'''
__author__ = 'guozhiwei'
import sys
import sysv_ipc
import struct
import time
import traceback
import logging

import env
env.init_env()

from ip_helper import get_local_ip
import log_helper
import data_report_with_sysv


LONG_LONG_SIZE = 8
UNSIGN_INT_SIZE = 4

SEMAPHORE_KEY = 1026
SHARED_MEMORY_KEY = 1026

LOCAL_IP = get_local_ip()


def get_semaphore():
    try:
        semaphore = sysv_ipc.Semaphore(SEMAPHORE_KEY,sysv_ipc.IPC_CREX)
    except sysv_ipc.ExistentialError:
        semaphore = sysv_ipc.Semaphore(SEMAPHORE_KEY)
        while not semaphore.o_time:
            time.sleep(.1)
    else:
        semaphore.release()
    return semaphore


def get_sysv_memory():
    try:
        memory = sysv_ipc.SharedMemory(SHARED_MEMORY_KEY,sysv_ipc.IPC_CREX)
    except sysv_ipc.ExistentialError:
        memory = sysv_ipc.SharedMemory(SHARED_MEMORY_KEY)
    return memory


def read():
    if time.strftime("%H:%M") == "00:00":
        #0点的时刻不要去上报了 方便绘图
        return
    semaphore = get_semaphore()
    memory = get_sysv_memory()
    try:
        semaphore.acquire(10)
        data = memory.read(UNSIGN_INT_SIZE)
        ss = struct.unpack("!I",data)
        if ss and ss[0] > 200000:
            logging.error(" too long  > 200000")
            semaphore.release()
            return
        readed_real_data = memory.read(ss[0] + UNSIGN_INT_SIZE)
        semaphore.release()
        format = "!I%dQ"%(ss[0]/LONG_LONG_SIZE)
        real_data = struct.unpack(format, readed_real_data)
        real_key_value_data = real_data[1:]
        logging.debug("real_key_value_data %s",real_key_value_data)
        num = 0
        key_value_dict = {}
        for i in range(0, len(real_key_value_data) ):
            if num % 2 == 0:
                key_value_dict[real_key_value_data[i]] = real_key_value_data[i+1]
                num += 1
                logging.info("key:%s value:%s", real_key_value_data[i], real_key_value_data[i + 1])
            else:
                num = 0
        for i in key_value_dict.items():
            report_db(i[0], i[1] , LOCAL_IP)
            data_report_with_sysv.set(i[0],0)
    except sysv_ipc.BusyError:
        semaphore.release()
        logging.debug("busy error")
    except:
        semaphore.release()
        logging.error(traceback.format_exc())


def report_db(itil_id, itil_value, itil_ip): # params = {
    #这里上报数据
    pass
    return
    #     'itil_id' : itil_id,
    #     'itil_value' : itil_value,
    #     'itil_ip' : itil_ip,
    # }
    # rs = http_helper.request_service('/itil/insert_data', params)
    # if rs.get('code') != 0:
    #     logging.error("itil_id:%s insert_data ret:%s",itil_id,rs.get('code'))
    # return rs

if __name__ == '__main__':
    LOG_PATH = './collect_itil_value.log'
    log_helper.addTimedRotatingFileHandler(LOG_PATH,'',logLevel='INFO')
    stime = time.time()
    logging.info('start')
    read()
    logging.info('end,cost:%.3f seconds', time.time() - stime)
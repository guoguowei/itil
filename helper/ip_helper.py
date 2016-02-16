#coding=utf8
__author__ = 'guozhiwei'
import socket
import struct
import logging
import traceback


def get_real_ip(request):
    ip = request.headers.get('X-Real-Ip', request.remote_addr)
    if not ip:
        ip = '9.9.9.9'
    return ip



def get_local_ip(ifname='eth0'):
    try:
        import fcntl
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
        ret = socket.inet_ntoa(inet[20:24])
        return ret
    except:
        logging.error(traceback.format_exc())
        return 'unknow local ip'
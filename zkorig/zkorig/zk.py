
import pytz
import datetime

t1 = datetime.datetime.now()

import binascii

from struct import unpack

import sys
import zklib
import time
import zkconst
import zkextendoplog


zk = zklib.ZKLib("192.168.1.15", 4370)
ret = zk.connect()
print ("connection:", ret)
print ( datetime.datetime.now() - t1 )
print (zk.version())
print ( datetime.datetime.now() - t1 )
#zk.disconnect()

zk.enableDevice()

command = zkconst.CMD_ATTLOG_RRQ
command_string = ''
chksum = 0
session_id = zk.session_id
reply_id = unpack('HHHH', zk.data_recv[:8])[3]
buf = zk.createHeader(command, chksum, session_id,
                      reply_id, command_string)
zk.zkclient.sendto(buf, zk.address)
zk.data_recv, addr = zk.zkclient.recvfrom(1024)
command = unpack('HHHH', zk.data_recv[:8])[0]
print ( datetime.datetime.now() - t1 )

if command == zkconst.CMD_PREPARE_DATA:
    size = unpack('I', zk.data_recv[8:12])[0]
    zk_size = size
else:
    zk_size = False

print ( datetime.datetime.now() - t1 )


if zk_size:
    bytes = zk_size
    while bytes > 0:
        #data_recv, addr = zk.zkclient.recvfrom(102400)
        data_recv, addr = zk.zkclient.recvfrom(1032)
#        print(  bytes )

        zk.attendancedata.append(data_recv)
        bytes -= 1024
    #zk.session_id = unpack('HHHH', zk.data_recv[:8])[2]
    #data_recv = zk.zkclient.recvfrom(8)
attendance = []
print ( datetime.datetime.now() - t1 )

if len(zk.attendancedata) > 0:
    # The first 4 bytes don't seem to be related to the user
    for x in range(len(zk.attendancedata)):
        if x > 0:
            zk.attendancedata[x] = zk.attendancedata[x][8:]
    attendancedata = b''.join(zk.attendancedata) 
    attendancedata = attendancedata[14:] 
    while len(attendancedata) > 0:
        uid, state, timestamp, space = unpack('24s1s4s11s', attendancedata.ljust(40)[:40])
        pls = unpack('c', attendancedata[29:30])
        uid = uid.split(b'\x00', 1)[0].decode('utf-8')
        tmp = ''
        for i in reversed(range(int(len(binascii.hexlify(timestamp)) / 2))):
            tmp += binascii.hexlify(timestamp).decode('utf-8')[i * 2:(i * 2) + 2] 
        #print(  tmp )

        attendance.append((uid, int(binascii.hexlify(state), 16),
                           zkconst.decode_time(int(tmp, 16)), unpack('HHHH', space[:8])[0]))
        
        attendancedata = attendancedata[40:]
print ( datetime.datetime.now() - t1 )
print( attendance )

command = zkconst.CMD_CLEAR_ATTLOG
command_string = ''
chksum = 0
session_id = zk.session_id
reply_id = unpack('HHHH', zk.data_recv[:8])[3]
buf = zk.createHeader(command, chksum, session_id,
                      reply_id, command_string)
zk.zkclient.sendto(buf, zk.address)
zk.data_recv, addr = zk.zkclient.recvfrom(1024)
command = unpack('HHHH', zk.data_recv[:8])[0]
print( command )
print ( datetime.datetime.now() - t1 )

zk.disableDevice()
zk.disconnect()
print ( datetime.datetime.now() - t1 )

import pytz
import datetime, time


import binascii

from struct import unpack

import sys
import zklib
import time
import zkconst
import zkextendoplog




while True:
    #t1 = datetime.datetime.now()

    zk = zklib.ZKLib("192.168.1.15", 4370)
    ret = zk.connect()
    session_id = zk.session_id
    #print ("connection:", ret)

    reply_id = unpack('HHHH', zk.data_recv[:8])[3]
    buf = zk.createHeader( zkconst.CMD_ATTLOG_RRQ, 0, session_id, reply_id, '')
    zk.zkclient.sendto(buf, zk.address)
    zk.data_recv, addr = zk.zkclient.recvfrom(1024)

    #print( zk.data_recv )
    
    zk_size = False
    if unpack('HHHH', zk.data_recv[:8])[0] == zkconst.CMD_PREPARE_DATA:
        zk_size = unpack('I', zk.data_recv[8:12])[0]

    if zk_size:
        while zk_size > 0:
            data_recv, addr = zk.zkclient.recvfrom(1032)
            zk.attendancedata.append(data_recv)
            zk_size -= 1024

    #print( zk.attendancedata )
    attendance = []

    if len(zk.attendancedata) > 0:
        # The first 4 bytes don't seem to be related to the user
        for x in range(len(zk.attendancedata)):
            if x > 0:
                zk.attendancedata[x] = zk.attendancedata[x][8:]
        attendancedata = b''.join(zk.attendancedata) 
        attendancedata = attendancedata[14:] 
        i = len( attendancedata )
        i = i % 40
        if i == 0:
            i = 40
        a = attendancedata[-i:]
        uid, state, timestamp, space = unpack('24s1s4s11s', a.ljust(40))
        pls = unpack('c', a[29:30])
        uid = uid.split(b'\x00', 1)[0].decode('utf-8')
        tmp = ''
        for i in reversed(range(int(len(binascii.hexlify(timestamp)) / 2))):
            tmp += binascii.hexlify(timestamp).decode('utf-8')[i * 2:(i * 2) + 2] 
        aa = (uid, int(binascii.hexlify(state), 16), zkconst.decode_time(int(tmp, 16)), unpack('HHHH', space[:8])[0])
        print( aa )

        
        while len(attendancedata) > 0:
            uid, state, timestamp, space = unpack('24s1s4s11s', attendancedata.ljust(40)[:40])
            pls = unpack('c', attendancedata[29:30])
            uid = uid.split(b'\x00', 1)[0].decode('utf-8')
            tmp = ''
            for i in reversed(range(int(len(binascii.hexlify(timestamp)) / 2))):
                tmp += binascii.hexlify(timestamp).decode('utf-8')[i * 2:(i * 2) + 2] 
            attendance.append((uid, int(binascii.hexlify(state), 16), zkconst.decode_time(int(tmp, 16)), unpack('HHHH', space[:8])[0]))
            attendancedata = attendancedata[40:]

    print( attendance )

    #reply_id = unpack('HHHH', zk.data_recv[:8])[3]
    #buf = zk.createHeader( zkconst.CMD_CLEAR_ATTLOG, 0, session_id, reply_id, '')
    #zk.zkclient.sendto(buf, zk.address)
    #zk.disconnect()    
    #zk.data_recv, addr = zk.zkclient.recvfrom(1024)
    #command = unpack('HHHH', zk.data_recv[:8])[0]
    #print( command )
    #print ( datetime.datetime.now() - t1 )
    #time.sleep( 1 )

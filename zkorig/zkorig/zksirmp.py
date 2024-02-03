import pytz
import datetime, time
import binascii
from struct import unpack
import sys
import zklib
import time
import zkconst
import zkextendoplog
from random import randint

import xmlrpc.client

od = -1
url = "http://127.0.0.1:8069"
db = "jia"
username = "auto"
password = "sics#admin"

while od == -1:
    try:
        oc = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format( url ))
        om = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format( url ))
        print( "Authenticating with MRP" )
        od = oc.authenticate( db, username, password, {} )
        print( "Fetching Data" )
        edict = om.execute_kw(db, od, password, 'simrp.employee', 'search_read', [[[ 'active', '=', True ]]], { 'fields': [ 'id', 'name', 'code', 'attcode', 'type' ] } )
        print( "E-Dict Loaded" )
        attcode = {}
        for e in edict:
            if e[ 'attcode' ]:
                attcode[ e[ 'attcode' ] ] = e[ 'id' ]
                
        print( attcode )
    except Exception as e:
        print( "Start Error: " + str( e ) )

while True:
    try:
        zk = zklib.ZKLib("192.168.1.15", 4370)
        ret = zk.connect()
        session_id = zk.session_id

        reply_id = unpack('HHHH', zk.data_recv[:8])[3]
        buf = zk.createHeader( zkconst.CMD_ATTLOG_RRQ, 0, session_id, reply_id, '')
        zk.zkclient.sendto(buf, zk.address)
        zk.data_recv, addr = zk.zkclient.recvfrom(1024)

        zk_size = False
        if unpack('HHHH', zk.data_recv[:8])[0] == zkconst.CMD_PREPARE_DATA:
            zk_size = unpack('I', zk.data_recv[8:12])[0]

        if zk_size:
            while zk_size > 0:
                data_recv, addr = zk.zkclient.recvfrom(1032)
                zk.attendancedata.append(data_recv)
                zk_size -= 1024

        aa = ()
        ecode = -1
        
        if len(zk.attendancedata) > 0:
            attendancedata = b''.join(zk.attendancedata) 
            attendancedata = attendancedata[14:] 
            i = len( attendancedata ) % 40
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
            if uid in attcode.keys():
                ecode = randint( 100000, 999999 )
                print( ecode )
                f = open( "..\id.js", "w" )
                f.write( 'var euid = "' + str( attcode[ uid ] ) + '"; var ecode = ' + str( ecode ) + ';' )
                f.close()
                
            

        reply_id = unpack('HHHH', zk.data_recv[:8])[3]
        buf = zk.createHeader( zkconst.CMD_CLEAR_ATTLOG, 0, session_id, reply_id, '')
        zk.zkclient.sendto(buf, zk.address)
        zk.disconnect()    
        #zk.data_recv, addr = zk.zkclient.recvfrom(1024)
        #command = unpack('HHHH', zk.data_recv[:8])[0]
        #print( command )
        #print ( datetime.datetime.now() - t1 )
        #time.sleep( 1 )
    except Exception as e:
        print( "Error: " + str( e ) )   
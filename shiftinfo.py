import datetime, time, pytz
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

DAYSTART = 6.00

BREAKLIST = [   { 'use': True, 'start': 12.00, 'end': 12.50, 'deduct': 30 },
                { 'use': True, 'start': 21.50, 'end': 22.00, 'deduct': 30 },
                { 'use': False, 'start': 23.50, 'end': 23.75, 'deduct': 15 },
                { 'use': False, 'start': 21.50, 'end': 22.00, 'deduct': 30 },
                { 'use': False, 'start': 21.50, 'end': 22.00, 'deduct': 30 } 
            ]

def getlocaltime( utctime, tzone ):
    usertz = pytz.timezone( tzone or str(pytz.utc) )
    return pytz.utc.localize( utctime ).astimezone( usertz )

def getnowlocaltimestring( o ):
    usertz = pytz.timezone( o.env.user.tz or str(pytz.utc) )
    return pytz.utc.localize( datetime.datetime.now() ).astimezone( usertz ).strftime( DEFAULT_SERVER_DATETIME_FORMAT )
    
def getShiftDay( dt, tzone ):
    dt = getlocaltime( dt, tzone )
    #_logger.info( ">>>>>>>>>>>>>>>>>>>ADT>>>> "  );
    #_logger.info( dt  );

    ltt = dt.hour + ( dt.minute / 60 )
    if ltt <= DAYSTART:
        dt = dt - datetime.timedelta(days=1)
    return dt
    
def getShiftTimeDiff2( stimeDT, etimeDT, tzone, deduct, activeTime ):
    localstarttime = stimeDT
    localendtime = etimeDT
    if tzone:
        localendtime = getlocaltime( etimeDT, tzone )
        localstarttime = getlocaltime( stimeDT, tzone )

    difftime = localendtime - localstarttime
    a = round( difftime.total_seconds() / 60 )
    _logger.info( ">>>>>>>>>>>>>>>>>>>A>>>> " + str( a ) );

    stime = localstarttime.hour + ( localstarttime.minute / 60 )
    etimeF = localendtime.hour + ( localendtime.minute / 60 )
    
    if activeTime:
        a = a - deduct
        for br in BREAKLIST:
            if br[ 'use' ]:
                e = 0
                if etimeF > stime:      #same day
                    e = checkEngulf( stime, etimeF, br[ 'start' ], br[ 'end' ] )
                else:
                    e = checkEngulf( stime, 24.00, br[ 'start' ], br[ 'end' ] )
                    e = e + checkEngulf( 0.00, etimeF, br[ 'start' ], br[ 'end' ] )
                if e > 0:
                    a = a - br[ 'deduct' ]
    if a < 0:
        a = 0
    return a


def getShiftTimeDiff( stimeDT, etimeF, tzone, deduct, activeTime ):



    #deprecated



    localstarttime = stimeDT
    if tzone:
        localstarttime = getlocaltime( stimeDT, tzone )
    stime = localstarttime.hour + ( localstarttime.minute / 60 )
    edate = localstarttime.date()
    if etimeF < stime:
        edate = edate + datetime.timedelta(days=1)
    edatetime = datetime.datetime( edate.year, edate.month, edate.day, int( etimeF ), round( ( etimeF - int( etimeF ) ) * 60 ), 0 )
     
    localstarttime = localstarttime.replace(tzinfo=None)
    difftime = edatetime - localstarttime
    
    a = round( difftime.total_seconds() / 60 )
    
    if activeTime:
        a = a - deduct
        for br in BREAKLIST:
            if br[ 'use' ]:
                e = 0
                if etimeF > stime:      #same day
                    e = checkEngulf( stime, etimeF, br[ 'start' ], br[ 'end' ] )
                else:
                    e = checkEngulf( stime, 24.00, br[ 'start' ], br[ 'end' ] )
                    e = e + checkEngulf( 0.00, etimeF, br[ 'start' ], br[ 'end' ] )
                if e > 0:
                    a = a - br[ 'deduct' ]

    #_logger.info( ">>>>>>>>>>>>>>>>>>>>>> activeTime: " + str( etimeF ) )
    #_logger.info( ">>>>>>>>>>>>>>>>>>>>>> localstart: " + localstarttime.strftime("%d-%b-%Y (%H:%M:%S.%f)") )
    #_logger.info( ">>>>>>>>>>>>>>>>>>>>>> edatetime: " + edatetime.strftime("%d-%b-%Y (%H:%M:%S.%f)") )
    #_logger.info( ">>>>>>>>>>>>>>>>>>>>>> activeTime: " + str( difftime ) )
    #_logger.info( ">>>>>>>>>>>>>>>>>>>>>> a: " + str( a ) )
    
    if a < 0:
        a = 0
    return a

def checkEngulf( rstartF, rendF, cstartF, cendF ):
    r = 1
    if cstartF < rstartF:
        r = 0
    if cendF > rendF:
        r = 0
    return r
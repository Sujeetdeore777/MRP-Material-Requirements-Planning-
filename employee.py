# -*- coding: utf-8 -*-

import datetime, time, json
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import shiftinfo
import calendar

class Bu( models.Model ):
    _name = 'simrp.bu'
    
    name = fields.Char( 'Code', required = True )
    buc = fields.Char( 'Bank Upload Code', size = 10 )
    bname = fields.Char( 'BU Name', size = 50 )
    
    def initemp( self ):
        es = self.env[ 'simrp.employee' ].search( [ ( 'active', 'in', [True, False] ) ] )
        for e in es:
            if not e.bu_:
                e.bu_ = self.id
    
class Employee(models.Model):
    _name = 'simrp.employee'
    
    code = fields.Char( 'Code', size = 20, readonly = True )
    name = fields.Char( 'Employee', size = 50, required = True )
    active = fields.Boolean( 'Active', default=True )
    salaryactive = fields.Boolean( 'Salary Active', default=True )
    bu_ = fields.Many2one( 'simrp.bu', 'BU', required = True )
    doj = fields.Date( 'Join Date', default=lambda self: fields.Date.today(), required = True )

    attcode = fields.Char( 'ATT Code', size=5 )
    gender = fields.Selection( [
            ( 'm', 'Male' ),
            ( 'f', 'Female' ),
            ], 'Gender', default='m', required = True )
    salarytype = fields.Selection( [
            ( 'm', 'Monthly' ),
            ( 'd', 'Daily' ),
            ], 'Salarytype', default='d', required = True )

    # state = fields.Selection( [
            # ( 'n', 'Data Record' ),
            # ( 'l', 'Data Locked' ),
            # ], 'State', default='n', required = True )
            
    type = fields.Selection( [
            ( 'a', 'Admin' ),
            ( 'p', 'Production' ),
            ( 's', 'Support' ),
            ], 'Role Type', default='p', required = True )
    
    lastuniformissue = fields.Date( 'Last Uniform Issue')
    shirt_apron_size = fields.Char( 'Shirt/Apron Size', size=20 )
    shoe_size = fields.Char( 'Shoe Size', size=20 )
    uniform_category = fields.Selection( [
            ( 'om', 'Office Male' ),
            ( 'of', 'Office Female' ),
            ( 'pm', 'Production Male' ),
            ( 'pf', 'Production Female' ),
            ], 'Uniform Category', default='pm', required = True )

    shift_ = fields.Many2one( 'simrp.shift', 'Shift Plan' )
    hourlybasis = fields.Boolean( 'Hourlybasis with OT?', default=False )
    espf = fields.Boolean( 'ESIC/PF?', default=False )
    workhours = fields.Float( 'Workhours', digits=(8,2), required = True )
    salary = fields.Float( 'Salary', digits=(8,2) )
    leaves = fields.Boolean( 'Paid Leaves?', default=False )
    bonus = fields.Boolean( 'Bonus?', default=False )
    contractparty_ = fields.Many2one( 'simrp.party', 'Contractor' )
    contractcost = fields.Float( 'Contract %', digits=(8,2), default=0 )
    log = fields.Text( 'Log', readonly = True, default='' )
    basewage = fields.Float( 'Base Wage for Slip', digits=(8,2), default=0 )
    modeofpay = fields.Selection( [
            ( 'bank', 'Bank' ),
            ( 'cash', 'Cash' ),
            ( 'con_bank', 'Bank to Contractor' ),
            ( 'con_cash', 'Cash to contractor' ),
            ], 'Mode of Pay', default='cash', required = True )
#    name_contractor = fields.Char( 'Contractor Name', size = 50 )
    aadhar_no = fields.Char( 'Aadhar Card No', size = 15 )
    
    bankac = fields.Char( 'Bank A/c No. **', default='' )
    bankifsc = fields.Char( 'Bank IFSC **', default='' )
    bankacname = fields.Char( 'Bank A/c Name.', default='' )
    bankphoto = fields.Binary( 'Bank Photo **', attachment=True )
    bankphotoname = fields.Char( 'Bank Photo Name' )
    
    dob = fields.Date( 'Date of Birth')
    panno = fields.Char('PAN No.', default="")
    # pre_company = fields.Char( 'Previous Company Name', size = 50 )

    hourcost = fields.Float( 'Hourcost', digits=(8,2), compute='_hourcost', store=True )
    daycost8 = fields.Float( 'Daycost 8hrs', digits=(8,2), compute='_daycost8', store=True )
    daycost115 = fields.Float( 'Daycost 11.5hrs', digits=(8,2), compute='_daycost115', store=True )

    homecontact = fields.Char( 'Contact', size = 50 )
    mobile = fields.Char( 'Mobile', size = 20 )
    localaddress = fields.Char( 'Local Address', size = 500 )
    homeaddress = fields.Char( 'Home Address', size = 500 )

    esicacno = fields.Char( 'ESIC A/c No', size = 50 )
    pfacno = fields.Char( 'PF A/c No', size = 50 )
    
    shahsyncid = fields.Integer( 'Shah DBid', default=-1 )
    _order = 'name'
    
    @api.multi
    @api.depends( 'salarytype', 'hourlybasis', 'espf', 'workhours', 'salary', 'contractparty_', 'contractcost', 'leaves', 'bonus' )
    def _daycost8( self ):
        for o in self:
            dsal = o.salary
            if o.salarytype == 'm':
                dsal = dsal / 26
            lb = 0
            if o.leaves:
                lb = dsal / 20        # 1 PL per every 20 days of work
            b = 0
            if o.bonus:
                if o.contractparty_:
                    b = 3000 / 12 / 26
                else:
                    b = ( dsal * 26 ) / 12 / 26
            esic = 0
            pf = 0
            if o.espf:
                esic = dsal * 0.0325
                pf = dsal * 0.65 * 0.13
            cc = 0
            if o.contractparty_:
                cc = ( dsal + esic + pf ) * o.contractcost / 100
                
            benefits = 5000 / 12 / 26
            dsal = dsal + lb + b + esic + pf + cc + benefits
            o.daycost8 = dsal

    @api.multi
    @api.depends( 'daycost8' )
    def _hourcost( self ):
        for o in self:
            if (o.workhours) and (o.workhours > 0):
                cost = o.daycost8 / o.workhours
            else:
                cost = o.daycost8 / 9
            o.hourcost = cost

    # @api.multi
    # def lock( self ):
        # for o in self:
            # o.state = 'l'

    # @api.multi
    # def open( self ):
        # for o in self:
            # o.state = 'n'
            
    @api.multi
    @api.depends( 'daycost8' )
    def _daycost115( self ):
        for o in self:
            if o.hourlybasis:
                o.daycost115 = o.hourcost * 11.5
            else:
                o.daycost115 = o.daycost8
            
    @api.model
    def create(self, vals):
        emplock = self.env['ir.config_parameter'].sudo().get_param('employeesynclock') or False
        if ( emplock ) and ( 'code' not in vals ):
            raise exceptions.UserError( 'Employees are auto synced. Cannot modify [c]' )
        if 'code' not in vals:
            vals['code'] = self.env['ir.sequence'].next_by_code('simrp.employee')
        o = super(Employee, self).create(vals)
        if not emplock:
            self.env[ 'simrp.auditlog' ].log( o, 'Create Employee:', {} )
        return o

    @api.multi 
    def write(self, vals): 
        emplock = self.env['ir.config_parameter'].sudo().get_param('employeesynclock') or False
        if ( emplock ) and ( 'code' not in vals ):
            raise exceptions.UserError( 'Employees are auto synced. Cannot modify [w]' )
        if 'log' not in vals:
            if not emplock:
                self.env[ 'simrp.auditlog' ].log( self, 'Change Employee:', vals )
        return super().write(vals)

    def syncemployee( self, eid, ecode, ename, buid, gender, roletype, salarytype, workhours, active ):
        valsd = { 'name': ename, 'bu_': buid, 'gender': gender, 
                   'salarytype': salarytype, 'type': roletype, 
                   'workhours': workhours, 'code': ecode,
                   'active': active }
        rid = eid
        if eid > 0:
            e = self.search( [ ( 'id','=',eid ),'|',('active','=',True),('active','=',False) ] )
            _logger.info( 'CCCCCCCCCCCCCC EMPL CCCCCCCCCCCCCC Write: ' + e.name )
            e.write( valsd )
        else:
            #_logger.info( 'CCCCCCCCCCCCCC EMPL CCCCCCCCCCCCCC Create: ' + ename )
            e = self.create( valsd )
            rid = e.id
        return rid
    
    # @api.model
    # def logrecord( self ):
        # d = shiftinfo.getlocaltime( self.write_date, self.env.user.tz )
        # s = '[' + d.strftime("%b %d %Y") + '] ' + ( 'active' if self.active else 'INACTIVE' ) + '// ' 
        # s = s + self.name + ' (' + self.code + ') // ' + str( self.doj ) + ' // '
        # s = s + self.salarytype + '~' + ( 'hourly+OT' if self.hourlybasis else 'fullDay' )
        # s = s + ( '~ESPF' if self.espf else '~notRegistered' )
        # s = s + '~' + str( self.workhours ) + 'hrs, [ ' + str(self.salary) + ' ]\r\n'
        # if not self.log:
            # self.log = ''
        # self.log = self.log + s

    @api.multi
    def inPanel( self ):
        ntnow = fields.Datetime.now()
        dt = shiftinfo.getShiftDay( ntnow, self.env.user.tz )

        asearch = self.env[ 'simrp.attendance' ].search( [ ( 'adate', '=', dt.date() ), ( 'employee_', '=', self.id ) ] )
        if len( asearch ) == 0:
            a = self.env[ 'simrp.attendance' ].create( {
                'employee_': self.id,
                'adate': dt.date(),
                'hhin': dt.hour,
                'mmin': dt.minute,
                'autoflag': True,
            } )
            a._present()
            _logger.info( "################################## IN " + self.name )
        else:
            ar = asearch[ 0 ]
            if ar.state == 'l':                   #already out
                if not ar.log:
                    ar.log = ''
                ar.log = ar.log + ' ##### In: ' + str( ar.hhin ) + ':' + str( ar.mmin ) + ' Out: ' + str( ar.hhout ) + ':' + str( ar.mmout )
                ar.hhin = dt.hour
                ar.mmin = dt.minute
                ar.state = 'i'
                ar.hhout = 0
                ar.mmout = 0
                ar._present()
                ar.logflag = True
        return True

    @api.multi
    def outPanel( self ):
        ntnow = fields.Datetime.now()
        dt = shiftinfo.getShiftDay( ntnow, self.env.user.tz )

        dt = dt - datetime.timedelta(days=1)            # last 2 days

        asearch = self.env[ 'simrp.attendance' ].search( [ ( 'adate', '>=', dt.date() ), ( 'employee_', '=', self.id ), ( 'state', '=', 'i' ) ] )
        if len( asearch ) > 0:
            asearch[ 0 ].hhout = dt.hour
            asearch[ 0 ].mmout = dt.minute
            asearch[ 0 ].state = 'l'
            asearch[ 0 ]._present()
            _logger.info( "################################## OUT " + self.name )
        return True

    @api.multi
    def unactivate(self):
        self.active = False
        return True

    def salaryinactive(self):
        self.salaryactive = False
        return True

    def getemployeeperformance(self, startphp, endphp):
        datadic = {}
        k = 0
        proddic={}
        emp = self.env[ 'simrp.employee' ].search( [ ('active','=',True), ('type','=','p') ] )
        prod = self.env[ 'simrp.woproduction' ].search( [('pstime', '>=', startphp), ('petime1', '<=', endphp) ] )
        j = 1
        for p in prod:
            dic = {}
            dic['id'] = p.id
            dic['empid'] = p.employee_.id
            dic['okqty'] = p.okqty
            dic['itspeed'] = p.itspeed
            dic['pstime'] = p.pstime
            dic['petime1'] = p.petime1
            dic1 = {str(j) : dic}
            proddic.update(dic1)
            j = j + 1
        for e in emp:
            d = {}
            d['id'] = e.id
            d['name'] = e.name
            d['gender'] = e.gender
            # d['totalworkhours'] = e.workhours
            sd = datetime.datetime.strptime(str(startphp),'%Y-%m-%d')
            ss = sd.date()
            ed = datetime.datetime.strptime(str(endphp),'%Y-%m-%d')
            ee = ed.date()
            tempdate = ss
            s1 = ss.day
            e1 = ee.day
            totalmonthavgper = 0
            t_cnt = 0
            avg =0

            for i in range(int(s1), int(e1)+1):
                dt = tempdate.replace(day = int(i)) 
                start = datetime.datetime.combine(dt, datetime.datetime.min.time())
                end = datetime.datetime.combine(dt, datetime.datetime.max.time())
                opperformance = 0
                for pr in proddic:
                    if proddic[pr]['empid'] == e.id:
                        if proddic[pr]['pstime'] >= start and proddic[pr]['petime1'] <= end:
                            if proddic[pr]['itspeed']:
                                opperformance = proddic[pr]['okqty'] / proddic[pr]['itspeed']
                                if opperformance:
                                    t_cnt = t_cnt + 1
                                totalmonthavgper = totalmonthavgper + opperformance
                d[ i ] = round(opperformance,2)
            if totalmonthavgper:
                totalmavg = round(totalmonthavgper, 2)
                avg = totalmavg/ t_cnt
            else:
                avg = 0
            if d['gender'] == 'm':
                d['totalworkhours'] = 11.5
                d['workexpect'] = round((d['totalworkhours']/100)*95,1)
            else:
                d['totalworkhours'] = 10.5
                d['workexpect'] = round((d['totalworkhours']/100)*95,1)
            d['total']= round(avg, 2)
            per = round((d['total']/d['totalworkhours'])*100,2)
            # _logger.info("Total per     " +str(per))
            d['percent'] = round(per, 0)
            # _logger.info("Total percent     " +str(d['total']))
            dic2 = {str(k) : d}
            k =k + 1
            datadic.update(dic2)
        _logger.info("Total date emp detail array     " +str(datadic))
        return json.dumps(datadic)

class Opperformance(models.TransientModel):
    _name = 'simrp.opperformance'
    _description = 'Monthly Operator performance Report'
    _inherit = 'report.report_xlsx.abstract'
    
    sdate = fields.Date( 'Select month date', default=lambda self: fields.Date.today(), required = True )
    datadicperformance = fields.Text( 'DatadicPerformance' )
    datadicperf = fields.Text( 'DatadicPerformance' )
    htmltext = fields.Text( 'Data' )
    empreporthtml = fields.Text( 'report' )
    
    def generateNew( self ):
        for o in self:
            # _logger.info(o)
            date = o.sdate
            proddic = {}
            datadic = {}
            j = 1
            k = 1
            start_date = datetime.datetime(date.year, date.month, 1)
            end_date = datetime.datetime(date.year, date.month, calendar.mdays[date.month])
            # _logger.info( str(start_date) + "    " + str(end_date))
            
            emp = self.env[ 'simrp.employee' ].search( [ ('active','=',True), ('type','=','p') ] )
            prod = self.env[ 'simrp.woproduction' ].search( [('pstime', '>=', start_date), ('petime1', '<=', end_date) ] )
            # _logger.info(prod)
            for p in prod:
                dic = {}
                dic['id'] = p.id
                dic['empid'] = p.employee_.id
                dic['okqty'] = p.okqty
                dic['day'] = p.productionday
                dic['itspeed'] = p.itspeed
                dic['pstime'] = p.pstime
                dic['petime1'] = p.petime1
                dic1 = {str(j) : dic}
                proddic.update(dic1)
                j = j + 1
                
            ss = start_date.date()
            ee = end_date.date()
            tempdate = ss
            s1 = ss.day
            e1 = ee.day 
            
            # daydic = { '': 0, '': 0, '': 0, 'nextdate':0}
            emptydic = { 'name': '-', 'totalworkhours': 0, 'workexpect': 0, 'total': 0, 'percent': 0}
            
            for i in range(int(s1), int(e1)+1):
                dt = tempdate.replace(day = int(i)) 
                start = datetime.datetime.combine(dt, datetime.datetime.min.time())
                end = datetime.datetime.combine(dt, datetime.datetime.max.time())
                nextdate = dt.strftime('%a')
                
                emptydic[ str(i) ] = { 'w': 0 }
                _logger.info("Next day : " +str(nextdate))
            datadic[ 0 ] = emptydic
            for e in emp:
                if e.id not in datadic.keys():
                    datadic[ e.id ] = { 'name': e.name, 'totalworkhours': 0, 'workexpect': 0, 'total': 0, 'percent': 0}
                    for i in range(int(s1), int(e1)+1):
                        datadic[e.id][ str(i) ] = { 'w': 0 }
                    # _logger.info(datadic    )
                    
                    if e.gender == 'm':
                        datadic[ e.id ]['totalworkhours'] = 11.5
                        datadic[ e.id ]['workexpect'] = round((datadic[ e.id ]['totalworkhours']/100)*95,1)
                    else:
                        datadic[ e.id ]['totalworkhours'] = 10.5
                        datadic[ e.id ]['workexpect'] = round((datadic[ e.id ]['totalworkhours']/100)*95,1)
            o.datadicperf = json.dumps(datadic)
           
            totalmonthavgper = 0
            t_cnt = 0
            avg =0
            for pr in proddic:
                e = int(proddic[pr]['empid'])
                if e in datadic.keys():
                    pdate = proddic[pr]['day']
                    day = int(pdate.strftime( '%d' ))
                    opperformance = round( proddic[pr]['okqty'] / proddic[pr]['itspeed'], 2)
                    time = (proddic[pr]['petime1'] - proddic[pr]['pstime']).total_seconds()
                    if e and (day <= e1):
                        datadic[ e ][ str(day) ]['w'] = datadic[ e ][ str(day) ]['w'] + opperformance
                        # datadic[ 0 ][ str(day) ]['w'] = datadic[ e ][ str(day) ]['w'] + opperformance
                        # datadic[ 0 ][ str(day) ]['p'] = datadic[ e ][ str(day) ]['p'] + time

            o.datadicperformance = json.dumps(datadic)
            _logger.info("***********" +str(o.datadicperformance))
            # _logger.info(datadic)
            o.opreporthtml()

    def htmltable( self ):
        for o in self:
            dphp = json.loads( o.datadicperformance )
            t = ""
            for i in dphp:
                s = "<table border='1' width='100%'><tr>"
                if str(i) == 'op':
                    heading = {}
                    for v in dphp[i]:
                        for k in dphp[i][v]:
                            s = s + "<th>" + str(k) + "</th>"
                    s = s + "</tr><tr>"
                    break
                else:
                    for z in dphp[i]:
                        s = s + "<th>"+ z +"</th>"
                    s = s + "</tr><tr>"
                    for v in dphp[i]:
                        if v:
                            if str(i) == 'op':
                                for k in dphp[i][v]:
                                    if dphp[i][v][k]:
                                        s = s + "<td>" + str(dphp[i][v][k]) + "</td>"
                                    else:
                                        s = s + "<td></td>"
                                s = s + "</tr><tr>"
                            else:
                                s = s + "<td>" + str(dphp[i][v]) + "</td>"
                    s = s + "</tr></table><br>"
                    t = t + s
                o.htmltext = t
    def opreporthtml( self ):
        rp = self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        cmd = ""
        with open( rp + '/simrp/opperformance.py', 'r') as file:
            cmd = file.read()
        for o in self:
            exec( cmd )
            

    def download( self ):
        for o in self:
            data = {}
            return self.env.ref('simrp.simrp_opperformance').report_action(self, data)

    def getreportpath( self ):
        return self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']

    def generate_xlsx_report(self, workbook, data, o):
        bold = workbook.add_format({'bold': True, 'border':1, 'align': 'center', 'bg_color': 'yellow'})
        f = '/simrp/opperformance.rx.py'
        if f != "":
            cmd = ""
            with open( self.getreportpath() + f, 'r') as file:
                cmd = file.read()
                _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )
            exec( cmd )
        r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
        r.sudo().report_file = o.sdate.strftime( '%d%m%Y' )
        
    # def action_open_url(self):
        # return {
            # 'name': ("Tracking"),
            # 'type': 'ir.actions.act_url',
            # 'url': 'http://jiaiot.vii.co.in:8169/web#action=88&cids=1&menu_id=69&model=iiot.machine&view_type=list', # Replace this with tracking link
            # 'target': 'new', # you can change target to current, self, new.. etc
        # }

class Shift(models.Model):
    _name = 'simrp.shift'
    
    name = fields.Char( 'Shift Name', size = 40, required = True )
    starttime = fields.Float( 'Start Time', digits=(8,2), required = True )
    endtime = fields.Float( 'End Time', digits=(8,2), required = True )

    _order = 'starttime'

class Attendance(models.Model):
    _name = 'simrp.attendance'
    
    employee_ = fields.Many2one( 'simrp.employee', 'Employee', domain=[('active', '=', True)], required = True )

    shift_ = fields.Many2one( 'simrp.shift', 'Shift Plan', readonly=True )

    adate = fields.Date( 'Date', default=lambda self: fields.Date.today() )
    amonth = fields.Char( 'Month', size = 20, compute='_amonth', store=True )
    hhin = fields.Integer( 'HH 24' )
    mmin = fields.Integer( ':MM In' )
    hhout = fields.Integer( 'HH 24' )
    mmout = fields.Integer( ':MM Out' )
    
    hadj = fields.Float( 'Hr Adj.', digits=(8,2), default=0 )
    type = fields.Selection( [
            ( 'p', 'present' ),
            ( 'h', 'halfday' ),
            ( 'l', 'late in' ),
            ( 'e', 'early out' ),
            ( 'a', 'absent' ),
            ( 'u', 'uninformed absent' ),
            ], 'Type', required = True, default='a' )
    
    state = fields.Selection( [
            ( 'i', 'In' ),
            ( 's', 'Submit' ),
            ( 'l', 'Out' ),
            ], 'State', default='i', readonly = True )
            
    present = fields.Float( 'Present', digits=(8,2), compute='_present' )
    ot = fields.Float( 'OT', digits=(8,2), compute='_present' )
    
    log = fields.Text( default="" )
    logflag = fields.Boolean( default = False )
    autoflag = fields.Boolean( default = False )
    
    _order = 'adate desc, id'
    
    _sql_constraints = [
        ('eadate', 'unique(employee_, adate)', "Record already exists for this employee and date!"),
    ]

    @api.model
    def getCurrentIN(self):
        ntnow = fields.Datetime.now()
        dt = shiftinfo.getShiftDay( ntnow, self.env.user.tz )

        dt = dt - datetime.timedelta(days=1)            # last 2 days

        asearch = self.search( [ ( 'adate', '>=', dt.date() ), ( 'state', '=', 'i' ) ] )
        return asearch.read( ['employee_', 'hhin', 'mmin'] )

    @api.multi
    def logshow( self ):
        r = self.log + ', [Create: ' + self.create_uid.name + ' ' + self.create_date.strftime( DEFAULT_SERVER_DATETIME_FORMAT ) + ', Modify: ' + self.write_uid.name + ' ' + self.write_date.strftime( DEFAULT_SERVER_DATETIME_FORMAT ) + ']'
        raise exceptions.UserError( r )
        
    @api.model 
    def create(self, vals): 
        if 'autoflag' not in vals.keys():
            vals[ 'log' ] = 'Manual Record create by ' + self.env.user.name + ' at ' + shiftinfo.getnowlocaltimestring( self )
        
        return super(Attendance, self).create(vals)


    @api.multi 
    def write(self, vals): 
        #if self.state == 'l':
        #    raise exceptions.UserError( 'Attendance record already Locked' )
        #if self.create_date.date() != fields.Date.today():
        #    raise exceptions.UserError( 'Attendance modification only allowed on same day of entry.' )
        super(Attendance, self).write(vals)
        return True
    
    @api.multi
    @api.depends( 'adate' )
    def _amonth( self ):
        for o in self:
            o.amonth = o.adate.strftime('%B-%Y')
            
    @api.constrains( 'hhin', 'mmin', 'hhout', 'mmout' )
    def _validate(self):
        for o in self:
            if not ( 0 <= o.hhin <= 23 ):
                raise ValidationError( 'HH 0-23, MM 0-59' )
            if not ( 0 <= o.hhout <= 23 ):
                raise ValidationError( 'HH 0-23, MM 0-59' )
            if not ( 0 <= o.mmin <= 59 ):
                raise ValidationError( 'HH 0-23, MM 0-59' )
            if not ( 0 <= o.mmout <= 59 ):
                raise ValidationError( 'HH 0-23, MM 0-59' )
                
    @api.multi
    @api.depends( 'employee_', 'employee_.hourlybasis', 'employee_.workhours', 'adate', 'hhin', 'mmin', 'hhout', 'mmout', 'hadj' )
    def _present( self ):
        #_logger.info( '>>>>>>>>>>>>>>>>EEEEEEEEEEEEE ' )
        for o in self:
            if not ( 0 <= o.hhin <= 23 ):
                raise exceptions.UserError( 'HH 0-23, MM 0-59' )
            if not ( 0 <= o.hhout <= 23 ):
                raise exceptions.UserError( 'HH 0-23, MM 0-59' )
            if not ( 0 <= o.mmin <= 59 ):
                raise exceptions.UserError( 'HH 0-23, MM 0-59' )
            if not ( 0 <= o.mmout <= 59 ):
                raise exceptions.UserError( 'HH 0-23, MM 0-59' )

            o.present = 0
            o.type = 'a'
            o.ot = 0
            if not ( ( o.hhin == o.hhout ) and ( o.mmin == o.mmout ) ):
                stimeDT = datetime.datetime( o.adate.year, o.adate.month, o.adate.day, o.hhin, o.mmin, 0 )
                etimeF = o.hhout + ( o.mmout / 60 )
                d = shiftinfo.getShiftTimeDiff( stimeDT, etimeF, False, 0, True ) / 60
                d = d + o.hadj
                d = round( d * 4 ) / 4
                ot = d - o.employee_.workhours
                ot = round( ot * 4 ) / 4
                #_logger.info( '>>>>>>>>>>>>>>>>>>DDDDDDDDD ' + str(d) )
                if not o.employee_.hourlybasis:
                    if d >= 6:
                        o.present = 1
                        o.type = 'p'
                    if ( 0 < d < 6 ):
                        o.present = 0.5
                        o.type = 'h'
                if o.employee_.hourlybasis:
                    if d > 0:
                        o.present = 1
                        o.type = 'p'
                        o.ot = ot

    @api.multi 
    def markout( self ): 
        self.state = 'l'
        self.log = self.log + '\nManual Out done by ' + self.env.user.name + ' at ' + shiftinfo.getnowlocaltimestring( self )
        self.autoflag = False        
        self._present()


class Tattendanceday(models.TransientModel):
    _name = 'simrp.tattendanceday'
    
    tdate = fields.Date( 'Tdate', default=lambda self: fields.Date.today(), required = True )
    dest = fields.Text( 'Action:', compute='_dest' )
    
    @api.multi
    @api.depends( 'tdate' )
    def _dest( self ):
        for o in self:
            d = 'Generating Blank attendance on above date, records for: \r\n\r\n'
            es = self.env[ 'simrp.employee' ].search( [ ( 'active', '=', True ) ] )
            i = 0
            for e in es:
                i = i + 1;
                d = d + e.name + ' [' + e.code + ']\r\n'
            d = d + '\r\n ' + str( i ) + ' employees'
            o.dest = d
    
    @api.multi 
    def generate( self ): 
        asearch = self.env[ 'simrp.attendance' ].search( [ ( 'adate', '=', self.tdate ) ] )
        if len( asearch ) > 0:
            raise exceptions.UserError( 'This date attendance entry already exists. Proceed Manually' )
        es = self.env[ 'simrp.employee' ].search( [ ( 'active', '=', True ) ] )
        for e in es:
            self.env[ 'simrp.attendance' ].create( {
                'employee_': e.id,
                'adate': self.tdate,
            } )
                #'shift_': e.shift_.id,
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance Records for ' + str( self.tdate ),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'simrp.attendance',
            'target': 'new',
            'domain': [('adate','=',self.tdate)],
           }

    
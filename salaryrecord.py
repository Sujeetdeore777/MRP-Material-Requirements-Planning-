
import datetime, time
import calendar
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_round
import base64, json
import logging
_logger = logging.getLogger(__name__)

class EmpSalary(models.Model):
    _name = 'simrp.monthempsalary'
    
    month_end = fields.Date( 'Month End Date', required = True )
    bu_ = fields.Many2one( 'simrp.bu', 'BU' )
    name = fields.Char(compute='_xname', store=True)
    
    monthpt = fields.Integer( 'Month PT', digits=(8,2), default=200, required=True)
    weeklyoff = fields.Integer( 'Weekly Off', digits=(8,2), required=True, default=4)
    ph_workdays = fields.Float( 'PH Work days', digits=(8,2), required=True, default=0)
    ph_weeklyoff = fields.Float( 'PH Weekly Off', digits=(8,2), required=True, default=0)
    
    month_days = fields.Float( 'Month Days', digits=(8,2), compute='_calc')
    salary_days = fields.Float( 'Salary Days', digits=(8,2), compute='_calc')
    Attend_days = fields.Float( 'Attend Days', digits=(8,2), compute='_calc')
    employee_ = fields.Many2one( 'simrp.employee', 'Employee')
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'c', 'Attendance, Deductions, Advances Reivew' ),
            ( 's', 'Submit' ),
            ( 'l', 'Locked' ),
            ], 'State', default='d', readonly = True )

    # salaryrecord_s = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees', domain=[('contractparty_','=',False)])
    # salaryrecord_s_other = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'Contract Employees', domain=[('contractparty_','!=',False)])

    salaryrecord_s_att = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees' )
    salaryrecord_s_calc = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees' )
    salaryrecord_s_deduct = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees' )
    salaryrecord_s_advance = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees' )
    salaryrecord_s_slip = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees', domain=[('employee_.contractparty_','=',False)] )
    salaryrecord_s_summary = fields.One2many( 'simrp.salaryrecord', 'monthempsalary_', 'BU Employees' )   

    bankfile = fields.Binary( 'Bank File' )
    bankfilename = fields.Char( 'Bank File Name' )

    summary = fields.Text( 'Summary', readonly = True )
    _sql_constraints = [ ('unique_mes', 'unique (month_end, bu_)', 'Period already exists for this BU!') ]

    @api.depends('month_end' )
    def _xname(self):
        for o in self:
            r = ''
            if o.month_end:
                # r = '[' + o.bu_.name + '] ' + o.month_end.strftime( '%Y-%m-%d' )
                r = o.month_end.strftime( '%Y-%m-%d' )
            o.name = r

    def bankfilegen( self ):
        if self.bu_:
            buc = self.bu_.buc
            bname = self.bu_.bname
            bf = ''
            for r in self.salaryrecord_s_slip:
                if r.selectgenerate:
                    if ( not r.employee_.bankac ) or ( not r.employee_.bankifsc ):
                        raise exceptions.UserError('Employee bank details not available' )
                    acn = r.employee_.bankacname if r.employee_.bankacname else r.employee_.name
                    bf = bf + 'N,,' + r.employee_.bankac + ',' + "{:.2f}".format(abs( r.net_pay )) + ',' + acn
                    bf = bf + ',,,,,,,,' + bname + ',' + acn[:20] + ',,,,,,,,,' + fields.date.today().strftime("%d/%m/%Y")
                    bf = bf + ',,' + r.employee_.bankifsc + ',,,' + '\n'
                    r.chq_no = 'bank'
                    r.selectgenerate = False
            _logger.info( bf )
            self.bankfile = base64.b64encode( bf.encode('utf-8') )
            self.bankfilename = buc + "_bank_" + bname + "_" + fields.Datetime.now().strftime("%m%d%Y%H%M%S") + ".csv"
        return True

    def submit( self ):
        self.updateall()
        self.state = 's'
    
    def lock( self ):
        self.state = 'l'
        
    def unlock( self ):
        self.state = 'c'
        
    @api.depends('month_end', 'weeklyoff', 'ph_workdays')
    def _calc(self):
        for o in self:
            d = o.month_end
            if d:
                o.month_days = d.day
                o.salary_days = o.month_days - o.weeklyoff
                o.Attend_days = o.salary_days - o.ph_workdays

    def single_employee(self):
        for e in self.employee_:
            self.create_salary_record( e )
            self.employee_ = False
        self.state = 'c'
        return True

    def loadallemployees(self):
        # emp = self.env['simrp.employee'].search( [ ('salaryactive', '=', True), ( 'bu_','=',self.bu_.id ) ] )
        # emp = self.env['simrp.employee'].search( [ '|', ( 'active', '=', True ), ( 'active', '=', False ), ('salaryactive', '=', True) ] )
        emp = self.env['simrp.employee'].search( [] )
        self.state = 'c'
        for e in emp:
            self.create_salary_record( e )
            _logger.info( e.name )
        return True

    def create_salary_record(self, e):
        salary_entry = self.env['simrp.salaryrecord'].search( [ ('employee_', '=', e.id), ('monthempsalary_','=',self.id) ] )
        if not salary_entry:
            line = self.env[ 'simrp.salaryrecord' ].create( {
                'monthempsalary_': self.id,
                'employee_': e.id,
                'month_end': self.month_end,
                'month_days': self.month_days,
                'monthpt': self.monthpt,
            } )
            line._calc()
        return True

    def salaryslip(self):
        return self.env.ref('simrp.action_report_salaryslip').report_action(self)

    def updateall(self):
        st = {}
        for o in self.salaryrecord_s_att:
            o._calc()
            if o.bu_.name not in st:
                st[ o.bu_.name ] = {}
            conname = '-'
            if o.contractparty_:
                conname = o.contractparty_.name
            if conname not in st[ o.bu_.name ]:
                st[ o.bu_.name ][ conname ] = 0
            st[ o.bu_.name ][ conname ] = st[ o.bu_.name ][ conname ] + o.net_pay
        
        s = ''
        for b in st:
            for c in st[ b ]:
                s = s + b + '[' + c + '] ' + str( st[ b ][ c ] ) + '\n'
        
        self.summary = s



class SalaryRecord(models.Model):
    _name = 'simrp.salaryrecord'

    monthempsalary_ = fields.Many2one( 'simrp.monthempsalary', 'Month Record', readonly = True )

    month_end = fields.Date( 'Month End Date',default=lambda self: fields.Date.today(), required = True )
    month_days = fields.Float( 'Month Days', digits=(8,2))
    monthpt = fields.Float( 'Month PT', digits=(8,2))
    
    employee_ = fields.Many2one( 'simrp.employee', 'Employee', readonly = True )
    contractparty_ = fields.Many2one( related='employee_.contractparty_' )
    bu_ = fields.Many2one( related='employee_.bu_' )
    code = fields.Char( related='employee_.code')

    # state = fields.Selection( [
            # ( 'i', 'Init' ),
            # ( 'c', 'Checked' )
            # ], 'State', default='i', readonly = True )

    #instance of employee master
    bankac = fields.Char( related='employee_.bankac' )
    workhr = fields.Float( related='employee_.workhours' )    
    espf = fields.Boolean( related='employee_.espf')
    salarytype = fields.Selection( related='employee_.salarytype' )
    
    agreed_salary = fields.Float( 'Agreed Salary', digits=(8,2),readonly = True)
    netperhrs = fields.Float( 'Net/hr', digits=(8,2), readonly = True)
    perday_salary = fields.Float( 'Per day salary', digits=(8,2), readonly = True)
    present_days = fields.Float( 'Present Days', digits=(8,2), readonly = True)
    ot = fields.Float( 'OT', digits=(8,2), readonly = True)
    pay_days = fields.Float( 'Pay Days', digits=(8,2), readonly = True)
    ph_flag = fields.Boolean( 'PH Flag', default= True )
    pay = fields.Float( 'Pay', digits=(8,2), readonly = True)
    otpay = fields.Float( 'OT Pay', digits=(8,2), readonly = True)
    grosspay = fields.Float( 'Gross', digits=(8,2), readonly = True)
    wages = fields.Float( 'Wages', digits=(8,2))
    hra = fields.Float( 'HRA', digits=(8,2))
    conv = fields.Float( 'Conv', digits=(8,2))
    uniform = fields.Float( 'Uniform', digits=(8,2))
    medical = fields.Float( 'Medical', digits=(8,2))
    others = fields.Float( 'OT/Others', digits=(8,2), readonly = True)
    esic = fields.Float( 'ESIC', digits=(8,2), readonly = True)
    pf = fields.Float( 'PF', digits=(8,2), readonly = True)

    adjdays = fields.Float( 'M.Adj. Days', digits=(8,2))
    adjot = fields.Float( 'M.Adj. OT', digits=(8,2))
    notes = fields.Text( 'Notes' )
    stardays = fields.Integer( 'Star Reward' )
    u_absent = fields.Integer( 'uAbsent' )
    incident_amt = fields.Integer( 'Incident Amount')
    leave_encashment = fields.Integer( 'Leave Encashment')
    annual_bg = fields.Integer( 'Bonus/Gift' )
    addpenaltyreward = fields.Integer( 'Penalty')
    add_nonslip = fields.Integer( 'Additional NonSlip' )
    
    adv_deduction_s = fields.One2many( 'simrp.empadvance', 'salaryrecord_', 'Advance Deductions' )
    net_pay = fields.Float( 'Net Pay', digits=(8,2), readonly = True)
    tds = fields.Float( 'TDS', digits=(8,2))
    lwf = fields.Float( 'LWF', digits=(8,2))
    esic_contri = fields.Float( 'ESIC contri', digits=(8,2), readonly = True)
    pf_contri = fields.Float( 'PF contri', digits=(8,2), readonly = True)
    attend_register = fields.Float( 'Attend', digits=(8,2), readonly = True)

    incident_s = fields.One2many( 'simrp.incident', 'employee_', 'Incident',compute='_calc' )
    leave_s = fields.One2many( 'simrp.leave_req', 'employee_', 'Leave Record',compute='_calc' )
    attendance_s = fields.One2many( 'simrp.attendance', 'employee_', 'Attendance',compute='_calc' )
    # auto_days = fields.Float( 'Auto Days', digits=(8,2), compute='_calc')
    NetA = fields.Float( 'NetA', digits=(8,2), compute='_calc')
    uabsentdays = fields.Integer( 'UIDay', compute='_calc')
    auto_days = fields.Float( 'Auto Days', digits=(8,2), compute='_calc')
    auto_ot = fields.Float( 'Auto OT', digits=(8,2), compute='_calc')
    adv_deduction = fields.Float( 'Adv.Deduct', digits=(8,2), compute='_calc')
    openadvance = fields.Float( 'OpenAdv', digits=(8,2), compute='_calc')
    aprleaves_count = fields.Float( 'Aprv.LR', digits=(8,2), compute='_calc')
    total_deduction = fields.Float( 'Deductions', digits=(8,2), compute='_calc')
    advancebal = fields.Float( 'Advance Balance', digits=(8,2), compute='_calc')
    incident_count = fields.Float( 'Incidents', digits=(8,2), compute='_calc')
    postworkdays = fields.Char( 'PostWork', compute='_calc')

    selectgenerate = fields.Boolean( 'BankGen?' )
    chq_no = fields.Char( 'Chq / Txn No.')

    _order = 'contractparty_, employee_'

    def dummy( self ):
        return True

    def month_pt( self, gender, salary):
        pt = self.monthempsalary_.monthpt
        if gender == 'm':
            if salary < 7500:
                pt = 0
            elif (salary < 10000):
                pt = 175
        elif gender == 'f':
            if salary < 10000:
                pt = 0
        return pt


    def _calc(self):
        for o in self:
            days = 0
            ot = 0
            date = o.month_end
            post = 0
            pre = 0
            adv = 0
            aprleavecount = 0
            incidentcount = 0
            if date:
                start_date = datetime.datetime(date.year, date.month, 1)
                attendance = self.env['simrp.attendance'].search( [ ('adate', '>=',start_date), ('adate', '<=',o.month_end ), ('employee_', '=', o.employee_.id) ] )
                post = self.env['simrp.attendance'].search_count( [ ('adate', '>=', o.month_end ), ('employee_', '=', o.employee_.id), ('type','=','p') ] )
                pre = self.env['simrp.attendance'].search_count( [ ('adate', '<', start_date ), ('employee_', '=', o.employee_.id), ('type','=','p') ] )
                leave = self.env['simrp.leave_req'].search( [ ('from_date', '>=',start_date), ('from_date', '<=',o.month_end ), ('employee_', '=', o.employee_.id), ('status','=','Approved') ] )
                incidents = self.env['simrp.incident'].search( [ ('datetime', '>=',start_date), ('datetime', '<=',o.month_end ), ('employee_', '=', o.employee_.id) ] )
                incidentcount = len( incidents )
                aprleavecount = len( leave )
                
                for i in attendance:
                    days = days + i.present
                    ot = ot + i.ot

                ears = self.env['simrp.empadvance'].search( [ ('docdate', '<=',o.month_end ), ('employee_', '=', o.employee_.id) ] )
                for ea in ears:
                    adv = adv + ea.amount

                o.leave_s = leave
                o.attendance_s = attendance
                o.incident_s = incidents

            o.uabsentdays = o.monthempsalary_.Attend_days - days - aprleavecount
            if o.uabsentdays < 0:
                o.uabsentdays = 0
            
            o.openadvance = adv
            o.aprleaves_count = aprleavecount
            o.incident_count = incidentcount
            o.auto_ot = ot
            o.auto_days = days
            o.postworkdays = o.employee_.name + " [" + str( pre ) + ">" + str( days ) + "<" + str( post ) + "]"

            adamt = 0
            for a in o.adv_deduction_s:
                adamt = adamt - a.amount
            o.adv_deduction = adamt

            # abamt = 0
            # # for a in o.advance_s:
                # # amt = amt + a.bal_amount
            # o.advancebal = abamt

            c = o
            c.present_days = c.auto_days + c.adjdays
            c.ot = c.auto_ot + c.adjot
            if c.ph_flag:
                c.pay_days = c.present_days + c.monthempsalary_.ph_workdays + c.monthempsalary_.ph_weeklyoff
            elif not c.ph_flag:
                c.pay_days = c.present_days
            c.otpay = c.ot * c.netperhrs

            if c.salarytype == 'd':
                if c.employee_.basewage > 1:
                    c.wages = c.grosspay / 1.75
                    c.hra = c.wages * 0.5
                    c.uniform = c.wages * 0.02
                    c.conv = c.wages * 0.03
                    gender = c.employee_.gender
                    c.monthpt = c.month_pt( gender, c.grosspay)
                    c.attend_register = c.wages / c.employee_.basewage
                else:
                    c.wages = 0
                    c.hra = 0
                    c.uniform = 0
                    c.conv = 0
                    c.monthpt = 0
                c.netperhrs = c.employee_.salary / c.workhr
                c.perday_salary = c.employee_.salary
                c.pay = c.employee_.salary * c.pay_days
                c.grosspay = round( c.pay + c.otpay )
                if c.employee_.espf:
                    c.others = c.wages * 0.3
                    c.esic = float_round((c.grosspay * 0.0075),precision_digits=None, precision_rounding=1, rounding_method='UP' )
                    c.pf = (c.wages + c.conv + c.uniform + c.medical )* 0.12
                    c.esic_contri = round(c.grosspay * 0.0325)
                    c.pf_contri = round(c.pf /12*13)
            else:
                c.wages = c.employee_.basewage / c.monthempsalary_.salary_days * c.pay_days
                c.hra = c.wages * 0.5
                c.uniform = c.wages * 0.02
                c.conv = c.wages * 0.05
                c.medical = c.wages * 0.05
                c.attend_register = c.pay_days
                gender = c.employee_.gender
                c.monthpt = c.month_pt( gender , c.grosspay)
                c.agreed_salary = c.employee_.salary
                if c.monthempsalary_.salary_days:
                        if not c.employee_.hourlybasis:
                            c.netperhrs = ( c.agreed_salary / c.monthempsalary_.salary_days ) / c.workhr
                            c.perday_salary = c.agreed_salary / c.monthempsalary_.salary_days
                            c.pay = c.perday_salary * c.pay_days
                        else:
                            c.netperhrs = ( c.agreed_salary / c.monthempsalary_.salary_days ) / 11.5
                            c.perday_salary = ( c.agreed_salary / c.monthempsalary_.salary_days ) / 11.5 * 8
                            c.pay = c.perday_salary * c.pay_days
                c.grosspay = round( c.pay + c.otpay )
                if c.employee_.espf:
                    c.others = c.grosspay - (c.wages + c.hra + c.conv + c.uniform + c.medical)
                    c.esic = float_round((c.grosspay * 0.0075),precision_digits=None, precision_rounding=1, rounding_method='UP' )
                    c.pf = (c.wages + c.conv + c.uniform + c.medical )* 0.12
                    c.esic_contri = round(c.grosspay * 0.0325)
                    c.pf_contri = round(c.pf /12*13)
            
            statdeduction = c.esic + c.pf + c.monthpt + c.lwf + c.tds

            c.NetA = round(c.grosspay - statdeduction)
            c.total_deduction = c.add_nonslip - c.adv_deduction + c.leave_encashment + c.annual_bg + c.stardays - c.u_absent - c.addpenaltyreward
            c.net_pay = round(c.grosspay - statdeduction + c.total_deduction )


    # def checked(self):
        # self.state = 'c'
        # return True

    # def reset( self ):
        # self.state = 'i'

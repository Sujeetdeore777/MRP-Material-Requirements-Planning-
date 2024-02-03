# -*- coding: utf-8 -*-

import datetime, time
from odoo.exceptions import ValidationError
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import logging
import odoo.tools as tools
_logger = logging.getLogger(__name__)
from dateutil.rrule import rrule, MONTHLY, DAILY
import base64, json

class Tcustsummary(models.TransientModel):
    _name = 'simrp.tcustsummary'
    _inherit = 'report.report_xlsx.abstract'
    
    currentdate = fields.Date( 'Current Date', default=lambda self: fields.Date.today(), required = True )
    account_ = fields.Many2one( 'simrp.account', 'Select Account', readonly = True )
    tcustsummaryline = fields.One2many( 'simrp.tcustsummaryline', 'tcustsummary_', 'Accline', readonly = True )
    reporthtml = fields.Text( 'Report HTML', readonly = True, default='{}' )

    
    def custoutsmry(self):
        # _logger.info(party_.id)
        for o in self:
            accline = self.env['simrp.accline'].search( [ ] )
            party = self.env[ 'simrp.party' ].search( [ ('associate', '=', 'cust' ) ] )
            for p in party:
                # _logger.info(p.name)
                total_ledger = 0
                total_ledger1 = 0
                dueamount = 0
                balance = 0
                balance = 0
                ageing = 0
                badj = 0
                diff = 0
                unduebills = 0
                ageing15days = 0
                ageing15daysoverdue = 0
                ageing30daysoverdue = 0
                ageing60daysoverdue = 0
                ageing90daysoverdue = 0
                unadjpayments = 0
                for ac in accline:
                    if p.id == ac.account_.partyid:
                        total_ledger = total_ledger + ac.amountcr
                        total_ledger1 = total_ledger1 + ac.amountdr
                        badj = badj + ac.baladjAmount
                        balance = total_ledger1 - total_ledger
                        diff = balance - badj
                        unadjpayments = unadjpayments + ac.amountcr
                        caldate = (o.currentdate - ac.docdate).days
                        ageing = caldate - p.creditperiod
                        # _logger.info("Ageing "+str(ageing))
                        if caldate < p.creditperiod :
                            unduebills = unduebills + ac.amountdr
                        if caldate > p.creditperiod :
                            dueamount = balance - unduebills
                            if ageing > 0:
                                if ageing < 15:
                                    ageing15days = ageing15days + ac.amountdr
                                if ageing >= 15 and ageing < 30:
                                    ageing15daysoverdue = ageing15daysoverdue + ac.amountdr
                                if ageing >= 30 and ageing < 60:
                                    ageing30daysoverdue = ageing30daysoverdue + ac.amountdr
                                if ageing >= 60 and ageing < 90:
                                    ageing60daysoverdue = ageing60daysoverdue + ac.amountdr
                                if ageing >= 90:
                                    ageing90daysoverdue = ageing90daysoverdue + ac.amountdr
                # _logger.info("Ageing of 15 before 15 days " +str(ageing15days))
                dic = self.env[ 'simrp.tcustsummaryline' ].create( { 
                    'tcustsummary_': o.id,
                    'party_' : p.id,
                    'accline_': ac.id, 
                    'creditperiod': p.creditperiod, 
                    'badj': badj, 
                    'diff': diff, 
                    'currentdate' : str(o.currentdate),
                    'ageing15days' : ageing15days,
                    'ageing15daysoverdue' : ageing15daysoverdue,
                    'ageing30daysoverdue' : ageing30daysoverdue,
                    'ageing60daysoverdue' : ageing60daysoverdue,
                    'ageing90daysoverdue' : ageing90daysoverdue,
                    'balance': balance,
                    'dueamount': dueamount,
                    'unduebills': unduebills,
                    'unadjpayments': unadjpayments,
                        } )
            _logger.info("************" +str(dic))
            # o.reporthtml = json.dumps(dic)
        return True
            
    def downloadreport( self ):
        data = {}
        return self.env.ref('simrp.simrp_tcustsummary').report_action(self, data)

    def getreportpath( self ):
        return self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        
    def generate_xlsx_report(self, workbook, data, o):
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(data) )
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + tools.config['addons_path'] )
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + o._name )

        f = '/simrp/tcustsummary.rx.py'
            
        cmd = ""
        with open( self.getreportpath() + f, 'r') as file:
            cmd = file.read()
            _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )

        exec( cmd )
        r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
        # r.sudo().report_file = o.account_.name + '_' + o.sdate.strftime( '%d%m%Y' ) + '_' + o.edate.strftime( '%d%m%Y' )

class Tcustsummaryline(models.TransientModel):
    _name = 'simrp.tcustsummaryline'

    tcustsummary_ = fields.Many2one( 'simrp.tcustsummary', 'Tcustsummary', readonly = True )
    accline_ = fields.Many2one( 'simrp.accline', 'Accline', readonly = True )
    account_ = fields.Many2one( 'simrp.account', readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Customer Name', readonly = True )
    creditperiod = fields.Integer( related='party_.creditperiod' )
    currentdate = fields.Date( 'Date', readonly = True )
    ageing = fields.Integer('ageing')
    ageing15days = fields.Integer('15 days')
    ageing15daysoverdue = fields.Integer('15 days overdue')
    ageing30daysoverdue = fields.Integer('30 days overdue')
    ageing60daysoverdue = fields.Integer('60 days overdue')
    ageing90daysoverdue = fields.Integer('overdue above 90 days')
    docdate = fields.Date( 'Date', readonly = True )
    amountcr = fields.Float( 'Amount Cr', digits=(8,2), readonly = True )
    amountdr = fields.Float( 'Amount Dr', digits=(8,2), readonly = True )
    balance = fields.Float( 'Ledger Balance', digits=(8,2), readonly = True )
    dueamount = fields.Float( 'Overdue Amount', digits=(8,2), readonly = True )
    unduebills = fields.Float( 'Undue Bills', digits=(8,2), readonly = True )
    badj = fields.Float( 'Bills Adj.', digits=(8,2), readonly = True )
    diff = fields.Float( 'Diff.', digits=(8,2), readonly = True )
    unadjpayments = fields.Float( 'Unadj. Payments', digits=(8,2), readonly = True )
    
    _order = 'docdate'

class Tledger(models.TransientModel):
    _name = 'simrp.tledger'
    _inherit = 'report.report_xlsx.abstract'
    
    account_ = fields.Many2one( 'simrp.account', 'Select Account', required = True )
    
    drperiod = fields.Selection( [
            ( '3', 'Last 3 months' ),
            ( 'cy', 'Current FY' ),
            ( 'ly', 'Last FY' ),
            ( 'a', 'All time' ),
            ], 'Period' )
    
    sdate = fields.Date( 'From date', default=lambda self: fields.Date.today(), required = True )
    edate = fields.Date( 'To date', default=lambda self: fields.Date.today(), required = True )
    
    # type = fields.Selection( related='account_.type' )
    # opbal = fields.Float( related='account_.opbal' )
    opbalance = fields.Float('Opening balance', readonly = True )
    baladj = fields.Float('Balance Adj', readonly = True )
    closingamt = fields.Float( 'Closingamt' )
    clbalance = fields.Char('Closing balance', readonly = True )
    taccline_s = fields.One2many( 'simrp.tledgerline', 'tledger_', 'Accline', readonly = True )
    state = fields.Selection( [
            ( 'd', 'Data' ),
            ( 'c', 'Prepared' ),
            ], 'state', default='d', required = True )

    @api.onchange('drperiod')
    def _onchange_drperiod(self):
        t = fields.Date.today()
        ye = t.year + 1
        ys = t.year
        if t.month in [1,2,3]:
            ye = t.year
            ys = t.year - 1
        if self.drperiod == '3':
            self.edate = t
            self.sdate = self.edate + relativedelta(months=-3, day=1)
        if self.drperiod == 'cy':
            self.edate = datetime.date( ye, 3, 31 )
            self.sdate = datetime.date( ys, 4, 1 )
        if self.drperiod == 'ly':
            self.edate = datetime.date( ye - 1, 3, 31 )
            self.sdate = datetime.date( ys - 1, 4, 1 )
        if self.drperiod == 'a':
            self.edate = t
            self.sdate = datetime.date( 2020, 4, 1 )
    
    def generate(self):
        for rec in self:
            oldrs = self.env[ 'simrp.tledgerline' ].search( [] )
            for oldr in oldrs:
                oldr.unlink()


            amt_debit = 0.0
            amt_debit1 = 0.0
            amt_credit = 0.0
            amt_credit1 = 0.0
            badj = 0
            opbalance = 0.0
            acc = rec.account_.id
            Opening_balance = self.env['simrp.accline'].search( [ ('docdate', '<', rec.sdate), ( 'account_','=',acc ) ] )
            for a in Opening_balance:
                amt_debit = amt_debit + a.amountdr
                amt_credit = amt_credit + a.amountcr
                badj = badj + a.baladjAmount
            rec.opbalance = amt_debit - amt_credit
            rec.baladj = badj
            opdr = rec.opbalance
            opcr = 0
            if opdr < 0:
                opcr = -opdr
                opdr = 0
                
            self.env[ 'simrp.tledgerline' ].create( { 
                'tledger_': rec.id, 
                'docdate': rec.sdate, 
                'docdesc': 'Opening balance',
                'amountdr': opdr,
                'amountcr': opcr,
                'baladjAmount': badj,
                } )
            
            dr = self.env['simrp.accline'].search( [ ('docdate', '>=', rec.sdate), ('docdate', '<=', rec.edate), ( 'account_','=',acc ) ] )
            #rec.accline_s = dr
            for d in dr:
                self.env[ 'simrp.tledgerline' ].create( { 
                    'tledger_': rec.id, 
                    'accline_': d.id, 
                    'docdate': d.docdate, 
                    'docdesc': d.docdesc,
                    'amountdr': d.amountdr,
                    'amountcr': d.amountcr,
                    'baladjAmount': d.baladjAmount,
                    } )
                amt_debit1 = amt_debit1 + d.amountdr
                amt_credit1 = amt_credit1 + d.amountcr
            cb = rec.opbalance + ( amt_debit1 - amt_credit1 )
            rec.closingamt = cb
            s = ' Dr.'
            if cb < 0:
                cb = -cb
                s = ' Cr.'
            rec.clbalance = "{:.2f}".format( round( cb, 2 ) ) + s

            self.state = 'c'
            data = {}
        return True

    def downloadreport( self ):
        data = {}
        return self.env.ref('simrp.simrp_tledger').report_action(self, data)
    

    def makeroundingoffjv( self ):
        roffa = self.env['simrp.account'].search( [ ( 'code','=','ROFF' ) ])
        if not roffa:
            raise exceptions.UserError("ROFF - Rounding off Auto code not defined in account ledgers")

        jvamt = self.closingamt
        draccount = roffa.id
        craccount = self.account_.id
        if jvamt < 0:
            jvamt = jvamt * -1
            draccount = self.account_.id
            craccount = roffa.id

        if jvamt != 0:
            j = self.env[ 'simrp.jtransaction' ].create( {
                'jdate': self.edate,
                'draccount_': draccount,
                'craccount_': craccount,
                'des': 'Rounding off for ' + self.account_.name,
                'amount': jvamt,
                } )
            
            j.addline()
            self.generate()
        return True

    def reset( self ):
        self.state = 'd'

    def getreportpath( self ):
        return self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        
    def generate_xlsx_report(self, workbook, data, o):
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(data) )
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + tools.config['addons_path'] )
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + o._name )

        f = '/simrp/tledger.rx.py'
            
        cmd = ""
        with open( self.getreportpath() + f, 'r') as file:
            cmd = file.read()
            _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )

        exec( cmd )
        r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
        r.sudo().report_file = o.account_.name + '_' + o.sdate.strftime( '%d%m%Y' ) + '_' + o.edate.strftime( '%d%m%Y' )

class Tledgerline(models.TransientModel):
    _name = 'simrp.tledgerline'

    tledger_ = fields.Many2one( 'simrp.tledger', 'Tledger', readonly = True )
    accline_ = fields.Many2one( 'simrp.accline', 'Accline', readonly = True )
    
    ref_ = fields.Reference( related='accline_.ref_' )
    docdate = fields.Date( 'Date', readonly = True )
    account_ = fields.Many2one( related='accline_.account_' )
    docdesc = fields.Char( 'Doc Desc', size=200, readonly = True )
    accounttype = fields.Selection( related='accline_.account_.type' )
    amountdr = fields.Float( 'Amount Dr', digits=(8,2), readonly = True )
    amountcr = fields.Float( 'Amount Cr', digits=(8,2), readonly = True )
    baladjAmount = fields.Float( 'Balance Adj.', digits=(8,2), readonly = True )

    _order = 'docdate'


class Tbank(models.TransientModel):
    _name = 'simrp.tbank'
    
    fundaccount_ = fields.Many2one( 'simrp.account', 'Fund Account', required = True )
    sdate = fields.Date( 'From date', default=lambda self: fields.Date.today(), required = True )
    edate = fields.Date( 'To date', default=lambda self: fields.Date.today(), required = True )
    drperiod = fields.Selection( [
            ( '3', 'Last 3 months' ),
            ( 'cy', 'Current FY' ),
            ( 'ly', 'Last FY' ),
            ], 'Period' )
    state = fields.Selection( [
            ( 'd', 'Data' ),
            ( 'c', 'Prepared' ),
            ], 'state', default='d', required = True )

    opbalance = fields.Float('Opening balance', readonly = True )
    clbalance = fields.Float('Closing balance', readonly = True )
    ledclbalance = fields.Float('Ledger balance', readonly = True )
    
    fundtransaction_s = fields.One2many( 'simrp.fundtransaction', 'fundaccount_', 'Fundtransaction', compute="generate")
    fundtransaction_s_um = fields.One2many( 'simrp.fundtransaction', 'fundaccount_', 'Fundtransaction', compute="generate")
    fundtransaction_s_ua = fields.One2many( 'simrp.fundtransaction', 'fundaccount_', 'Fundtransaction', compute="generate")
    fundtransaction_s_uc = fields.One2many( 'simrp.fundtransaction', 'fundaccount_', 'Fundtransaction', compute="generate")

    filterstring = fields.Char( 'Filterstring', size = 200 )
    fundtransaction_s_filter = fields.One2many( 'simrp.fundtransaction', 'fundaccount_', 'Fundtransaction', compute="generatefilter")
    commonparty_ = fields.Many2one( 'simrp.account', 'Party / Account' )

    def reset( self ):
        self.state = 'd'


    @api.onchange('drperiod')
    def _onchange_drperiod(self):
        if self.drperiod == '3':
            self.edate = fields.Date.today()
            self.sdate = self.edate + relativedelta(months=-3, day=1)
        if self.drperiod == 'cy':
            self.edate = datetime.date( 2022, 3, 31 )
            self.sdate = datetime.date( 2021, 4, 1 )
        if self.drperiod == 'ly':
            self.edate = datetime.date( 2021, 3, 31 )
            self.sdate = datetime.date( 2020, 4, 1 )

    # def generatefilter1( self ):
        # return True
    
    def generatefilter( self ):
        if self.filterstring:
            self.fundtransaction_s_filter = self.env['simrp.fundtransaction'].search( [ ('ftdate', '>=', self.sdate), ('ftdate', '<=', self.edate), ( 'fundaccount_','=',self.fundaccount_.id ), ('statementid','ilike',self.filterstring) ], order='ftdate' )
            _logger.info( '############################' )
            _logger.info( len( self.fundtransaction_s_filter ) )
            # self.filterstring = False
        else:
            _logger.info( '############################HERE' )
            self.fundtransaction_s_filter = False
        return True

    def markparty( self ):
        if self.commonparty_:
            for ft in self.fundtransaction_s_filter:
                if ft.state == 'd':
                    ft.party_ = self.commonparty_.id
                    for r in ft.fundaccline_.refadj_s:
                        r.sudo().unlink()
                    ft.submit()
            self.commonparty_ = False
        return True

            
    def generate(self):        
        for rec in self:
            opbalance = 0.0
            clbalance = 0.0
            acc = rec.fundaccount_.id
            
            amt_debit = 0.0
            amt_credit = 0.0
            Opening_balance = self.env['simrp.accline'].search( [ ('docdate', '<', rec.sdate), ( 'account_','=',acc ) ] )
            for a in Opening_balance:
                amt_debit = amt_debit + a.amountdr
                amt_credit = amt_credit + a.amountcr
            rec.opbalance = amt_debit - amt_credit

            cbledger = self.env['simrp.accline'].search( [ ('docdate', '>=', rec.sdate), ('docdate', '<=', rec.edate), ( 'account_','=',acc ) ] )
            for a in cbledger:
                amt_debit = amt_debit + a.amountdr
                amt_credit = amt_credit + a.amountcr
            rec.ledclbalance = amt_debit - amt_credit

            # Opening_balance = self.env['simrp.fundtransaction'].search( [ ('ftdate', '<', rec.sdate), ( 'fundaccount_','=',acc ) ] )
            # for a in Opening_balance:
                # opbalance = a.da - a.wa
            # rec.opbalance = opbalance
            
            dr = self.env['simrp.fundtransaction'].search( [ ('ftdate', '>=', rec.sdate), ('ftdate', '<=', rec.edate), ( 'fundaccount_','=',acc ) ], order='ftdate' )
            rec.fundtransaction_s = dr
            rec.fundtransaction_s_um = self.env['simrp.fundtransaction'].search( [ ('ftdate', '>=', rec.sdate), ('ftdate', '<=', rec.edate), ( 'fundaccount_','=',acc ), ('state','!=','s') ] )
            rec.fundtransaction_s_ua = self.env['simrp.fundtransaction'].search( [ ('ftdate', '>=', rec.sdate), ('ftdate', '<=', rec.edate), ( 'fundaccount_','=',acc ), ('accounttype','=','p'),('baladjAmount','!=',0) ] )
            rec.fundtransaction_s_uc = self.env['simrp.fundtransaction'].search( [ ('ftdate', '>=', rec.sdate), ('ftdate', '<=', rec.edate), ( 'fundaccount_','=',acc ), ('da','=',0),('wa','=',0) ] )

            clbalance = 0
            for d in dr:
                clbalance = clbalance + d.da - d.wa
                
                #ftdate and docdate mismatch problem
                #remove this logic after correction
                if d.accline_s:
                    for a in d.accline_s:
                        if a.docdate != d.ftdate:
                            a._docdate()

            rec.clbalance = rec.opbalance + clbalance
            self.state = 'c'
        return True


class Treceivable(models.TransientModel):
    _name = 'simrp.treceivable'
    
    edate = fields.Date( 'To date', default=lambda self: fields.Date.today(), required = True )
    state = fields.Selection( [
            ( 'd', 'Data' ),
            ( 'c', 'Prepared' ),
            ], 'state', default='d', required = True )
    trecdetails_s = fields.One2many( 'simrp.trecdetails', 'treceivable_', 'Trecdetails', readonly = True, domain=[('category','=','t')] )
    trecdetails_s_other = fields.One2many( 'simrp.trecdetails', 'treceivable_', 'Trecdetails', readonly = True, domain=[('category','!=','t')] )
    
    def generate(self):
        self.state = 'c'
        parties = self.env['simrp.party'].search( [], order='name' )
        cnt = 0
        payt = 0
        duet = 0
        for p in parties:
            acclines = self.env['simrp.accline'].search( [ ( 'account_', '=', p.account_.id ) ], order='docdate' )

            billsupto = self.edate - datetime.timedelta( days=p.creditperiod )

            netledger = 0
            netdueamt = 0
            unadjdramt = 0
            for d in acclines:
                netledger = netledger + d.amountdr - d.amountcr
                if d.docdate <= billsupto:
                    netdueamt = netdueamt + d.baladjAmount
                if d.baladjAmount != 0:
                    unadjdramt = unadjdramt + d.baladjAmount
                    
            if ( (netledger > 5)  ):
                tpr = self.env[ 'simrp.trecdetails' ].create( {
                    'treceivable_': self.id,
                    'party_': p.id,                    
                    'credit': p.creditperiod,                    
                    'due_upto': billsupto,
                    'due_amt': netdueamt,
                    'net_ledger': netledger,                    
                    'unadj_dr': unadjdramt,
                } )
            
        return True



class Trecdetails(models.TransientModel):
    _name = 'simrp.trecdetails'

    treceivable_ = fields.Many2one( 'simrp.treceivable', 'Treceivable', readonly = True )
    
    party_ = fields.Many2one( 'simrp.party', 'Party',readonly = True)
    category = fields.Selection( related='party_.category' )

    credit = fields.Integer( 'Credit',readonly = True)
    due_upto = fields.Date( 'Due Upto',readonly = True )
    due_amt = fields.Float( 'Due Bills',readonly = True )
    net_ledger = fields.Float( 'Net Ledger',readonly = True )
    unadj_dr = fields.Float( 'Unadj. Dr',readonly = True )

    accline_s = fields.One2many( 'simrp.accline', 'account_', 'Accline', compute='_lines' )
    fundtransaction_s = fields.One2many( 'simrp.fundtransaction', 'party_', 'Fundtransaction', compute='_lines' )
    
    adjproblem = fields.Boolean( 'Adjproblem', compute='_adjproblem' )
    def _adjproblem( self ):
        for o in self:
            r = True
            if abs( o.unadj_dr - o.net_ledger ) > 1:
                r = False
                _logger.info( 'ADJJJJ ' + str( o.unadj_dr ) + ' ' + str( o.net_ledger ) )
            o.adjproblem = r

    def dummy( self ):
        return True
    
    def _lines( self ):
        for o in self:
            o.accline_s = self.env['simrp.accline'].search( [ ( 'account_', '=', o.party_.account_.id ), ('baladjAmount','!=',0) ], order='docdate' )
            o.fundtransaction_s = self.env['simrp.fundtransaction'].search( [ ( 'party_', '=', o.party_.account_.id ) ] )

# class Trecdetailstree(models.TransientModel):
    # _name = 'simrp.trecdetailstree'

    # trecdetails_ = fields.Many2one( 'simrp.trecdetails', 'Trecdetails', readonly = True )
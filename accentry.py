# -*- coding: utf-8 -*-

import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
import logging
_logger = logging.getLogger(__name__)

# ACCOUNT_TDS94_DC = 2
# ACCOUNT_TDS94_PG = 1

class Accentry(models.Model):
    _name = 'simrp.accentry'
    name = fields.Char( 'Dummry Record', size = 2 )

    #
    # This is just a helper class with dummy record id = 1, so that the functions can access the odoo ORM
    #

    @api.model
    def createline( self, ref, refid, accountid, adr, acr ):
        #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + ref )
        ref_str = ref.split( '.' )[1].split( ',' )[0] + "_"
        line = self.env[ 'simrp.accline' ].sudo().create( {
            'ref_': ref,
            'account_': accountid,
            'amountdr': adr,
            'amountcr': acr,
            ref_str: refid,
        } )
        return line

    @api.model
    def lineNewRef( self, line ):
        dd = fields.Date.today()
        if 'duedate' in line.ref_._fields:
            dd = line.ref_.duedate
        line.newrefname = 'T/' + line.ref_.name
        line.duedate = dd
        
    @api.model
    def initSale( self, refid, partyaccount_, basicamt, taxscheme_ ):
        if taxscheme_.gstcheck:
            if partyaccount_.gstno == "":
                raise exceptions.UserError('Party GST Information missing')
        ref = '%s,%s' % ( 'simrp.invoice', refid )
        tc = taxscheme_.compute( basicamt )
        taxamt = tc[ 'tax' ]
        netamt = basicamt + taxamt
        
        line = self.createline( ref, refid,                        partyaccount_.id,           netamt,                 0 )
        self.lineNewRef( line )
        
        self.createline( ref, refid,                        taxscheme_.account_.id,     0,                      tc[ 'ba1' ] )
        if tc[ 'ba2' ] > 0:
            self.createline( ref, refid,                    taxscheme_.account2_.id,    0,                      tc[ 'ba2' ] )
        for d in tc['printTaxes']:
            self.createline( ref, refid,                    d[ 'taxaccountid' ],        0,                      d[ 'taxamount' ] )
        return netamt
        
    @api.model
    def initDN( self, refid, partyaccount_, basicamt, taxscheme_ ):
        if taxscheme_.gstcheck:
            if partyaccount_.gstno == "":
                raise exceptions.UserError('Party GST Information missing')
        ref = '%s,%s' % ( 'simrp.debit', refid )
        tc = taxscheme_.compute( basicamt )
        taxamt = tc[ 'tax' ]
        netamt = basicamt + taxamt
        
        line = self.createline( ref, refid,                        partyaccount_.id,           netamt,                 0 )
        self.lineNewRef( line )

        self.createline( ref, refid,                        taxscheme_.account_.id,     0,                      tc[ 'ba1' ] )
        if tc[ 'ba2' ] > 0:
            self.createline( ref, refid,                    taxscheme_.account2_.id,    0,                      tc[ 'ba2' ] )
        for d in tc['printTaxes']:
            self.createline( ref, refid,                    d[ 'taxaccountid' ],        0,                      d[ 'taxamount' ] )
        return netamt

    @api.model
    def initCN( self, refid, partyaccount_, basicamt, taxscheme_ ):
        if taxscheme_.gstcheck:
            if partyaccount_.gstno == "":
                raise exceptions.UserError('Party GST Information missing')
        ref = '%s,%s' % ( 'simrp.credit', refid )
        tc = taxscheme_.compute( basicamt )
        taxamt = tc[ 'tax' ]
        netamt = basicamt + taxamt
        
        line = self.createline( ref, refid,                        partyaccount_.id,           0,                      netamt )
        self.lineNewRef( line )
        
        self.createline( ref, refid,                        taxscheme_.account_.id,     tc[ 'ba1' ],            0 )
        if tc[ 'ba2' ] > 0:
            self.createline( ref, refid,                    taxscheme_.account2_.id,    tc[ 'ba2' ],            0 )
        for d in tc['printTaxes']:
            self.createline( ref, refid,                    d[ 'taxaccountid' ],        d[ 'taxamount' ],       0 )
        return netamt

    @api.model
    def initPurchase( self, refid, partyaccount_, basicamt, netamt, tdsamt, tdsaccount_, taxd, purd ):
        ref = '%s,%s' % ( 'simrp.purchase', refid )
        lna = self.createline( ref, refid,                  partyaccount_.id,           0,                      netamt )
        self.lineNewRef( lna )
        
        if tdsamt > 0:
            # self.createline( ref, refid,                    ACCOUNT_TDS94_PG,           0,                      tdsamt )
            self.createline( ref, refid,                    tdsaccount_.id,             0,                      tdsamt )
            ltds = self.createline( ref, refid,             partyaccount_.id,           tdsamt,                 0 )
            # ltds.newrefname = 'TDS 94C'
            ltds.newrefname = tdsaccount_.code
            
            self.env[ 'simrp.refadj' ].create( {
                'accline_': ltds.id,
                'agstaccline_': lna.id,
                'adjAmount': -tdsamt
                } )
        for p in purd.keys():
            self.createline( ref, refid,                    p,                          purd[ p ],              0 )
        for t in taxd.keys():
            self.createline( ref, refid,                    t,                          taxd[ t ],              0 )
        return True

    @api.model
    def initCash( self, refid, type, outamt, outacc_, inacc_, expacc_):
        ref = '%s,%s' % ( 'simrp.cash', refid )
        if type == 'cash_tran':
            self.createline( ref, refid,                    outacc_.id,           0,                      outamt )
            self.createline( ref, refid,                    inacc_.id,           outamt,                      0 )
        if type == 'cash_exp':
            self.createline( ref, refid,                    outacc_.id,           0,                      outamt )
            self.createline( ref, refid,                    expacc_.id,          outamt,                      0 )
        return True


    @api.model
    def initTransport( self, refid, partyaccount_, basicamt, ltrp_ ):
        ref = '%s,%s' % ( 'simrp.transporttrip', refid )
        lna = self.createline( ref, refid,                  partyaccount_.id,           0,    basicamt)
        self.lineNewRef( lna )
        self.createline( ref, refid,                        ltrp_.id,         basicamt,               0 )
        return True

    @api.model
    def initFTN( self, refid, partyaccount_, fundaccount_, a, payFlag, des ):
        ref = '%s,%s' % ( 'simrp.fundtransaction', refid )
        #payment, payFlag=1, Dr party
        fline = self.createline( ref, refid,                        partyaccount_.id,           payFlag * a,            ( 1 - payFlag ) * a )
        fline.newrefname = des
        #payment, payFlag=1, Cr bank
        self.createline( ref, refid,                        fundaccount_.id,            ( 1 - payFlag ) * a,    payFlag * a )
        return fline.id

    @api.model
    def initJV( self, refid, draccount_, craccount_, a ):
        ref = '%s,%s' % ( 'simrp.jtransaction', refid )
        if draccount_:
            self.createline( ref, refid,                        draccount_.id,              a,                      0 )
        if craccount_:
            self.createline( ref, refid,                        craccount_.id,              0,                      a )
        return True

    @api.model
    def initEXP( self, refid, saleaccount_, partyaccount_, a ):
        ref = '%s,%s' % ( 'simrp.exportinv', refid )
        self.createline( ref, refid,                        partyaccount_.id,           a,                      0 )
        self.createline( ref, refid,                        saleaccount_.id,            0,                      a )
        return True
        
    # @api.model
    # def initIEX( self, refid, partyaccount_, fundaccount_, expenseaccount_, basicamt, tdsamt, payamount, tdsaccount_, taxscheme_ ):
        # if taxscheme_.gstcheck:
            # if partyaccount_.gstno == "":
                # raise exceptions.UserError('Party GST Information missing')
        # ref = '%s,%s' % ( 'simrp.indirectexpense', refid )
        # tc = taxscheme_.compute( basicamt )
        # taxamt = tc[ 'tax' ]
        # netamt = basicamt + taxamt

        # #expense tr
        # lna = self.createline( ref, refid,                  partyaccount_.id,           0,                      netamt )
        # self.lineNewRef( lna )
        
        # if tdsamt > 0:
            # self.createline( ref, refid,                    tdsaccount_.id,             0,                      tdsamt )
            # ltds = self.createline( ref, refid,             partyaccount_.id,           tdsamt,                 0 )
            # ltds.newrefname = tdsaccount_.name
            
            # self.env[ 'simrp.refadj' ].create( {
                # 'accline_': ltds.id,
                # 'agstaccline_': lna.id,
                # 'adjAmount': -tdsamt
                # } )
        # self.createline( ref, refid,                        expenseaccount_.id,         basicamt,               0 )
        # for d in tc['printTaxes']:
            # self.createline( ref, refid,                    d[ 'taxaccountid' ],        d[ 'taxamount' ],       0 )

        # #payment tr
        # #if fundaccount_:
        # #    lpay = self.createline( ref, refid,                 partyaccount_.id,           payamount,              0 )
        # #    self.env[ 'simrp.refadj' ].create( {
        # #        'accline_': lpay.id,
        # #        'agstaccline_': lna.id,
        # #        'adjAmount': -payamount
        # #        } )
        # #    self.createline( ref, refid,                        fundaccount_.id,            0,                      payamount )
        
        # return True


class Accline(models.Model):
    _name = 'simrp.accline'
    
    ref_ = fields.Reference( [
            ('simrp.dispatch', 'Dispatch'), 
            ('simrp.invoice', 'Invoice'), 
            ('simrp.debit', 'Debit Note'), 
            ('simrp.credit', 'Credit Note'), 
            ('simrp.purchase','Purchase'),
            ('simrp.fundtransaction', 'Fund Pay/Rec Transaction'),
            ('simrp.indirectexpense', 'Indirect Expenditure'),
            ('simrp.jtransaction', 'Journal Transaction'),
            ('simrp.closingbalance', 'Closing Balance'),
            ('simrp.transporttrip', 'Transport Trip'),
            ('simrp.cash', 'Cash Transaction'),
            ('simrp.exportinv', 'Export Transaction'),
            ], string='Document Ref', readonly = True )  
            
    invoice_ = fields.Many2one( 'simrp.invoice', 'Invoice', readonly = True )
    dispatch_ = fields.Many2one( 'simrp.dispatch', 'Dispatch', readonly = True )
    debit_ = fields.Many2one( 'simrp.debit', 'Debit', readonly = True )
    credit_ = fields.Many2one( 'simrp.credit', 'credit', readonly = True )
    purchase_ = fields.Many2one( 'simrp.purchase', 'Purchase', readonly = True )
    fundtransaction_ = fields.Many2one( 'simrp.fundtransaction', 'Fundtransaction', readonly = True )
    indirectexpense_ = fields.Many2one( 'simrp.indirectexpense', 'Indirectexpense', readonly = True )
    jtransaction_ = fields.Many2one( 'simrp.jtransaction', 'Jtransaction', readonly = True )
    closingbalance_ = fields.Many2one( 'simrp.closingbalance', 'Closingbalance', readonly = True )
    transporttrip_ = fields.Many2one( 'simrp.transporttrip', 'Transporttrip', readonly = True )
    cash_ = fields.Many2one( 'simrp.cash', 'Cash', readonly = True )
    exportinv_ = fields.Many2one( 'simrp.exportinv', 'Exportinv', readonly = True )
    
    tdate = fields.Date( 'Date', readonly = True, default=lambda self: fields.Date.today() )
    docdate = fields.Date( 'Doc Date', compute="_docdate", store=True )
    docdesc = fields.Char( 'Doc Desc', compute='_docdesc' )
    account_ = fields.Many2one( 'simrp.account', 'Account', readonly = True )
    accounttype = fields.Selection( related='account_.type' )
    amountdr = fields.Float( 'Amount Dr', digits=(8,2), readonly = True )
    amountcr = fields.Float( 'Amount Cr', digits=(8,2), readonly = True )    

    refamount = fields.Float( 'Refamount', digits=(8,2), compute="_refamount", store=True )
    newrefname = fields.Char( 'Ref Name', size = 40, readonly = True, default='' )
    duedate = fields.Date( 'Due date', readonly = True )
    refadj_s = fields.One2many( 'simrp.refadj', 'accline_', 'Reference Adjustment' )
    refadjo_s = fields.One2many( 'simrp.refadj', 'agstaccline_', 'Reference Adjustment o', readonly = True )
    adjAmount = fields.Float( 'Adjusted amount', digits=(8,2), compute='_adjAmount' )
    baladjAmount = fields.Float( 'Balance Adj.', digits=(8,2), compute='_baladjAmount', store=True )

    modaccount_ = fields.Many2one( 'simrp.account', 'Modification Account' )

    _order = 'docdate desc, id desc'
    
    def modifyaccount( self ):
        if self.modaccount_:
            self.account_ = self.modaccount_
            self.modaccount_ = False
            #TODO what about adjref entries?
            
    @api.multi
    @api.depends( 'ref_' )
    def _docdate(self):
        for o in self:
            if o.ref_._name == 'simrp.dispatch':
                o.docdate = o.ref_.invdate
            if o.ref_._name == 'simrp.invoice':
                o.docdate = o.ref_.invdate
            elif o.ref_._name == 'simrp.debit':
                o.docdate = o.ref_.rdate
            elif o.ref_._name == 'simrp.credit':
                o.docdate = o.ref_.cndate
            elif o.ref_._name == 'simrp.purchase':
                o.docdate = o.ref_.docdate
            elif o.ref_._name == 'simrp.fundtransaction':
                o.docdate = o.ref_.ftdate
            elif o.ref_._name == 'simrp.indirectexpense':
                o.docdate = o.ref_.docdate
            elif o.ref_._name == 'simrp.jtransaction':
                o.docdate = o.ref_.jdate
            elif o.ref_._name == 'simrp.closingbalance':
                o.docdate = o.tdate
            elif o.ref_._name == 'simrp.transporttrip':
                o.docdate = o.ref_.date
            elif o.ref_._name == 'simrp.cash':
                o.docdate = o.ref_.date
            elif o.ref_._name == 'simrp.exportinv':
                o.docdate = o.ref_.edate
            else:
                o.docdate = fields.Date.today()

    @api.depends( 'ref_' )
    def _docdesc(self):
        for o in self:
            ac1 = ""
            if o.ref_._name == 'simrp.dispatch':
                o.docdesc = 'Sales: '
                ac1 = o.ref_.party_.name
            if o.ref_._name == 'simrp.invoice':
                o.docdesc = 'Sales: '
                ac1 = o.ref_.party_.name
            elif o.ref_._name == 'simrp.debit':
                o.docdesc = 'Debit: '
                ac1 = o.ref_.party_.name
            elif o.ref_._name == 'simrp.credit':
                o.docdesc = 'Credit: '
                ac1 = o.ref_.party_.name
            elif o.ref_._name == 'simrp.purchase':
                o.docdesc = 'Purchase: '
                ac1 = o.ref_.party_.name
            elif o.ref_._name == 'simrp.fundtransaction':
                o.docdesc = o.ref_.fundaccount_.name
                if not o.docdesc:
                    o.docdesc = 'FT'
            elif o.ref_._name == 'simrp.indirectexpense':
                o.docdesc = 'IExp: '
                ac1 = o.ref_.party_.name
            elif o.ref_._name == 'simrp.jtransaction':
                o.docdesc = 'Journal'
            elif o.ref_._name == 'simrp.closingbalance':
                o.docdesc = 'Closing Balance'
            elif o.ref_._name == 'simrp.transporttrip':
                o.docdesc = 'Transport: '
                ac1 = o.ref_.party_.name
            elif o.ref_._name == 'simrp.cash':
                o.docdesc = 'Cash: '
                ac1 = o.ref_.cash_ledger_acc_out.name
            elif o.ref_._name == 'simrp.exportinv':
                o.docdesc = 'Export Sale: '
                ac1 = o.ref_.party_.name
            else:
                o.docdesc = 'Other'
            o.docdesc = o.docdesc + ac1
            if o.account_.name != ac1:
                o.docdesc = o.docdesc + ' [' + o.account_.name + ']'

    @api.multi
    @api.depends( 'amountdr','amountcr' )
    def _refamount(self):
        for o in self:
            # + = Dr, - = Cr
            o.refamount = o.amountdr - o.amountcr

    @api.multi
    @api.depends( 'refamount', 'refadj_s', 'refadj_s.adjAmount', 'refadjo_s', 'refadjo_s.adjAmount' )
    def _adjAmount(self):
        for o in self:
            aa = 0
            for adj in o.refadj_s:
                aa += adj.adjAmount
            for adj in o.refadjo_s:
                aa -= adj.adjAmount
            o.adjAmount = aa
    
    @api.multi
    @api.depends( 'refamount','adjAmount', 'refadj_s', 'refadj_s.adjAmount', 'refadjo_s', 'refadjo_s.adjAmount' )
    def _baladjAmount(self):
        for o in self:
            o.baladjAmount = round( o.refamount + o.adjAmount, 2 )

    @api.multi
    def name_get(self):
        result = []
        for o in self:
            name = o.ref_.name
            if o.newrefname:
                name = o.newrefname + ' [' + '{:.2f}'.format( o.baladjAmount ) + ']'
                if o.duedate:
                    name = name + ' ' + o.duedate.strftime('%d.%m.%Y')
            result.append( ( o.id, name ) )
        return result
        
    def delete(self):
        for o in self:
            for r in o.refadjo_s:
                r.unlink()
            for r in o.refadj_s:
                r.unlink()
            o.unlink()
        return True
            
class Refadj(models.Model):
    _name = 'simrp.refadj'
    
    accline_ = fields.Many2one( 'simrp.accline', 'Tx reference', readonly = True )
    agstaccline_ = fields.Many2one( 'simrp.accline', 'Agst Tx reference', required = True )
    adjAmount = fields.Float( 'Adjamount', digits=(8,2), required = True )

    @api.onchange('agstaccline_')
    def _onchange_agstaccline_(self):
        aa = 0
        if self.agstaccline_:
            aa = self.agstaccline_.baladjAmount
            #if aa > (-self.accline_.baladjAmount):
            #    aa = -self.accline_.baladjAmount
        self.adjAmount = aa
        

class Account(models.Model):
    _name = 'simrp.account'
    
    ACCOUNT_TYPES = [
            ( 'p', 'Party' ),                                             # 0  -+
            ( 'fund', 'Fund Asset' ),                                     # 1  +
            ( 'ex', 'Direct Expenditure' ),                               # 2  PL 
            ( 'iex', 'Indirect Expenditure' ),                            # 3  PL
            ( 'tax', 'Tax' ),                                             # 4  -
            ( 'purc', 'Basic Purchase' ),                                 # 5  PL
            ( 'sale', 'Basic Sales' ),                                    # 6  PL 
            ( 'oi', 'Other Income (Indirect)' ),                          # 7  PL
            ( 'tds', 'TDS Payable to Govt.' ),                            # 8  -
            ( 'tdsc', 'TDS Deducted by Customer (Asset)' ),               # 9  +
            ( 'cash', 'Cash in Hand'),                                    # 10 +
            ( 'cap', 'Capital Account'),                                  # 11 -
            ( 'loanliab', 'Loans (Liability)'),                           # 12 -
            ( 'loanasst', 'Advances (Asset)'),                            # 13 +
            ( 'liab', 'Other Liabilities'),                               # 14 -
            ( 'asst', 'Other Assets'),                                    # 15 +
            ( 'prov', 'Provisions' ),                                     # 16 -
            ( 'fa', 'Fixed Assets' ),                                     # 17 +
            ( 'inv', 'Investments' ),                                     # 18 +
            ( 'temp', 'Temporary / Suspense (Zero)'),                     # 19 -
            ( 'stk', 'Stock Valuation (Adj)'),                            # 20 PLBS
            ( 'pcap', 'Profit & Loss Capitalisation'),                    # 21 Special
            ]
            
    #HARD CODE AUTO CODES:
    # LTRP = Local Transport Expenditure Account
    
    name = fields.Char( 'Account Name', size = 100, required = True  )
    code = fields.Char( 'AutoCode', size = 10)
    type = fields.Selection( ACCOUNT_TYPES, 'Type', required = True, default='p' )
    gstno = fields.Char('GST No.', default="")
    panno = fields.Char('PAN No.', default="")
    monthly_budget = fields.Float( 'Monthly Budget', digits=(8,2))
    partyid = fields.Integer( 'Internal Pid', compute='_partyid' )
    
    _order = 'name'
    
    opbal = fields.Float( 'Data', digits=(8,2), default=0 )                 # tds - tds rate
    
    def doopbal( self ):
        if self.type == 'p':
            raise exceptions.UserError('This shortcut is only for non-party accounts')
        if self.opbal == 0:
            raise exceptions.UserError('Enter Op Balance to create')
        ors = self.env[ 'simrp.closingbalance' ].search( [ ( 'partyaccount_', '=', self.id ) ] )
        if ors:
            raise exceptions.UserError('Op Balance Record Already exists')
        rec = self.env[ 'simrp.closingbalance' ].sudo().create( {
                'partyaccount_': self.id,
                'cdate': datetime.date(2020, 3, 31),
                'tamtdr': self.opbal if ( self.opbal > 0 ) else 0,
                'tamtcr': ( self.opbal * -1 ) if ( self.opbal < 0 ) else 0,
                'tdate': datetime.date(2020, 3, 31)
                } )
        rec.addlineac()
        self.opbal = False
        
    def _partyid( self ):
        for o in self:
            o.partyid = -9999999
            p = self.env[ 'simrp.party' ].search( [ ( 'account_', '=', o.id ) ] )
            if p:
                o.partyid = p.id
            
    @api.model
    def create( self, vals ):
        if ( 'gstno' not in vals ) and ( vals[ 'type' ] == 'p' ):
            raise exceptions.UserError('Party accounts cannot be created from here. Use Party Records')
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Account Create:', vals, False, False )
        return o

    def write(self, vals):
        if 'log' not in vals:
            self.env[ 'simrp.auditlog' ].log( self, 'Account Change:', vals, False, True )
        return super().write(vals)

class Closingbalance(models.Model):
    _name = 'simrp.closingbalance'
    
    partyaccount_ = fields.Many2one( 'simrp.account', 'Party / Account', required = True )
    name = fields.Char( 'Ref Name', readonly = True, default='CLBAL' )
    cdate = fields.Date( 'Cdate', default=lambda self: fields.Date.today() )
    
    tamtdr = fields.Float( 'Tamt Dr', digits=(8,2), default=0 )
    tamtcr = fields.Float( 'Tamt Cr', digits=(8,2), default=0 )
    tdate = fields.Date( 'Tdate' )
    tduedays = fields.Integer( 'Duedays' )
    trefname = fields.Char( 'Trefname', size = 40, default='' )
    
    accline_s = fields.One2many( 'simrp.accline', 'closingbalance_', 'Acc lines', readonly = True )
    amttot = fields.Float( 'Closing Amount', digits=(8,2), compute='_amttot' )
    
    def unlink( self ):
        for o in self:
            for a in o.accline_s:
                a.delete()
            o = super().unlink()

    @api.multi
    def _amttot( self ):
        for o in self:
            r = 0
            for al in o.accline_s:
                r = r + al.amountdr - al.amountcr
            o.amttot = r

    @api.multi
    def addline( self ):
        if not self.trefname:
            raise exceptions.UserError('Enter Bill Ref Details')
        if self.tamtcr + self.tamtdr <= 0:
            raise exceptions.UserError('Enter Bill Ref Details')

        ref = '%s,%s' % ( 'simrp.closingbalance', self.id )
        ref_str = 'closingbalance_'
        line = self.env[ 'simrp.accline' ].sudo().create( {
            'ref_': ref,
            'tdate': self.cdate,
            'account_': self.partyaccount_.id,
            'amountdr': self.tamtdr,
            'amountcr': self.tamtcr,
            ref_str: self.id,
        } )
        
        ddcr = self.tduedays
        ddate = self.tdate + relativedelta(days=+ddcr)
        line.newrefname = 'T/OP/' + self.trefname
        line.duedate = ddate
        
        self.tamtcr = 0
        self.tamtdr = 0
        self.trefname = ''
        return True

    def addlineac( self ):
        if self.partyaccount_.type == 'p':
            raise exceptions.UserError('Enter Bill Wise Details for parties and use the other button')

        ref = '%s,%s' % ( 'simrp.closingbalance', self.id )
        ref_str = 'closingbalance_'
        line = self.env[ 'simrp.accline' ].sudo().create( {
            'ref_': ref,
            'tdate': self.cdate,
            'account_': self.partyaccount_.id,
            'amountdr': self.tamtdr,
            'amountcr': self.tamtcr,
            ref_str: self.id,
        } )
        
        self.tamtcr = 0
        self.tamtdr = 0
        self.trefname = ''
        return True
    
class Fundtransaction(models.Model):
    _name = 'simrp.fundtransaction'
    
    name = fields.Char( 'Transaction Code', size = 20, readonly = True )
    statementid = fields.Char( 'Statement Id', size = 300, readonly = True )

    ftdate = fields.Date( 'Date', default=lambda self: fields.Date.today() )
    bdes = fields.Char( 'Narration', size = 150, default='' )
    bref = fields.Char( 'Chq./Ref.No.', size = 30, default='' )
    wa = fields.Float( 'Withdrawal Amt.', digits=(8,2), default=0 )
    da = fields.Float( 'Deposit Amt.', digits=(8,2), default=0 )
    cb = fields.Float( 'Closing Balance', digits=(8,2) )
    fundaccount_ = fields.Many2one( 'simrp.account', 'Fund Account', required = True )

    type = fields.Selection( [
            ( '1', 'Payment' ),
            ( '0', 'Receipt' ),
            ], 'Type', default='1', required = True )
    amount = fields.Float( 'Amount', digits=(8,2), required = True )
    
    party_ = fields.Many2one( 'simrp.account', 'Party / Account' )
    des = fields.Char( 'Description', size = 200 )
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 's', 'Submit' ),
            ], 'State', readonly = True, default='d' )
    
    accline_s = fields.One2many( 'simrp.accline', 'fundtransaction_', 'Acc lines' )
    fundaccline_ = fields.Many2one( 'simrp.accline', readonly=True )
    refadj_s = fields.One2many( related='fundaccline_.refadj_s' )
    baladjAmount = fields.Float( related='fundaccline_.baladjAmount' )
    accounttype = fields.Selection( related='party_.type' )

    tpayable_ = fields.Many2one( 'simrp.tpayable', 'tpayable')          # to link to payment wizard

    _sql_constraints = [
        ('unique_statementid', 'unique (statementid)', 'Duplicate Entry, Recheck')
    ]
    
    _order = 'ftdate desc'
    
    # def markopbal( self ):
        # if self.amount < 0:
            # self.wa = - self.amount
        # else:
            # self.da = self.amount
            
    @api.multi
    def name_get(self):
        result = []
        for o in self:
            name = o.name
            if o.party_:
                name = name + ', ' + o.party_.name 
            if o.amount:
                name = name + ', [' + '{:.2f}'.format( o.amount ) + ']'
            result.append( ( o.id, name ) )
        return result

    @api.multi
    def submit(self):
        for o in self:
            if o.party_:
                fid = self.env[ 'simrp.accentry' ].browse( 1 ).initFTN( o.id, o.party_, o.fundaccount_, o.amount, int( o.type ), o.des )
                o.fundaccline_ = fid
                o.state = 's'
  
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.fundtransaction')
        
        #if vals[ 'bdes' ]:
        #    vals['ftdate'] = datetime.datetime.strptime( vals['ftdate'], '%Y-%m-%d' ).strftime( '%Y-%d/%y' )
        # print( vals )
        
        desc = ''
        try:
            desc = '' + ( vals['bdes'] if 'bdes' in vals.keys() else vals[ 'des' ] )
        except:
            raise exceptions.UserError( 'Description is required' )
            
        vals['statementid'] = vals['ftdate'] + " ### " + desc + " ### " + ( vals['bref'] if 'bref' in vals.keys() else '' ) + " ### " + str( ( vals['wa'] if 'wa' in vals.keys() else 0 )  ) + " ### " + str( ( vals['da'] if 'da' in vals.keys() else 0 ) )
        
        _logger.info( '############# ' + vals['statementid'] )
        if 'wa' in vals.keys():
            vals['amount'] = vals['wa'] + vals['da']
            if vals['da'] > 0:
                vals['type'] = '0'        
        o = super(Fundtransaction, self).create(vals)
        
        return o

    @api.multi
    def reset( self ):
        for o in self:
            for al in o.accline_s:
                for ra in al.refadj_s:
                    ra.unlink()
                for ra in al.refadjo_s:
                    ra.unlink()
                al.unlink()
            o.party_ = False
            o.state = 'd'
        return True
    
    @api.multi
    def unlink( self ):
        for o in self:
            for al in o.accline_s:
                for ra in al.refadj_s:
                    ra.unlink()
                al.unlink()
            _logger.info( "################################################# Unlink: " + str( o.name ) )
        return super(Fundtransaction,self).unlink()

class Fthelper(models.TransientModel):
    _name = 'simrp.tfundsubmit'

    ft_ = fields.Many2one( 'simrp.fundtransaction', 'Fund Transaction', readonly = True )
    
    statementid = fields.Char( 'Statement Id', size = 300, readonly = True )
    type = fields.Selection( [
            ( '1', 'Payment' ),
            ( '0', 'Receipt' ),
            ], 'Type', default='1', readonly = True )
    amount = fields.Float( 'Amount', digits=(8,2), readonly = True )
    
    party_ = fields.Many2one( 'simrp.account', 'Party / Account' )
    des = fields.Char( 'Description', size = 200 )
    fundaccline_ = fields.Many2one( 'simrp.accline' )
    ref_s = fields.One2many( 'simrp.tfundsubmitline', 'fts_', 'Bill Reference' )
    v = fields.Integer()
    # unmarkamt = fields.Float( 'Unmarked Amt', digits=(8,2), compute='_unmarkamt' )

    # def dummy( self ):
        # return True
        

    def default_mergeft_( self ):
        #_logger.info( "################################################# DEF" )
        #_logger.info( str( self.env.context ) )
        # res = self.env[ 'simrp.fundtransaction' ].search( [ ('wa','=',0),('da','=',0),('amount','>',self.env.context[ 'default_amount' ] ), ('amount','<',self.env.context[ 'default_amount' ] )] )
        res = self.env[ 'simrp.fundtransaction' ].search( [ ('wa','=',0),('da','=',0),('amount','=',self.env.context[ 'default_amount' ] ) ] )
        return res and res[0] or False

    mergeft_ = fields.Many2one( 'simrp.fundtransaction', '[OR] Merge Transaction', default=default_mergeft_ )

    
        
    @api.model
    def default_get(self, fields_list):
        res = super(Fthelper, self).default_get(fields_list)
        if self.env.context[ 'default_party_' ]:
            rs = self.env[ 'simrp.accline' ].search( [('account_','=',self.env.context[ 'default_party_' ]), ( 'id', '!=', self.env.context[ 'default_fundaccline_' ]), ('baladjAmount','!=',0), ('newrefname','!=','')], order='docdate' )
            vals = []
            for r in rs:
                vals.append( ( 0, 0, {
                    'agstaccline_': r.id,
                    'docdate': r.docdate,
                    'origAmount': r.baladjAmount
                } ) )
            res.update({'ref_s': vals})
        return res
        
    @api.multi
    def mark( self ):
        _logger.info( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
        for r in self.ft_.fundaccline_.refadj_s:
            r.sudo().unlink()
        for r in self.ref_s:
            if r.check:
                self.env[ 'simrp.refadj' ].create( {
                    'accline_': self.ft_.fundaccline_.id,
                    'agstaccline_': r.agstaccline_.id,
                    'adjAmount': r.adjAmount
                } )
        return { 'type': 'ir.actions.act_view_reload' }
                    
    @api.multi
    def deletemerge( self ):
        self.mergeft_ = False
        self.allocate()
        
    @api.multi
    def allocate( self ):
        if self.party_:
            self.ft_.party_ = self.party_.id
            self.ft_.des = self.des
            for r in self.ft_.fundaccline_.refadj_s:
                r.sudo().unlink()
            self.ft_.submit()
        if self.mergeft_:
            if self.mergeft_.fundaccount_.id != self.ft_.fundaccount_.id:
                raise exceptions.UserError('Fund Account NOT Matching.')

            self.mergeft_.ftdate = self.ft_.ftdate
            self.mergeft_.wa = self.ft_.wa
            self.mergeft_.da = self.ft_.da
            self.mergeft_.cb = self.ft_.cb
            self.mergeft_.bdes = self.ft_.bdes
            self.mergeft_.bref = self.ft_.bref

            statementid1 = self.ft_.statementid         # since duplicate statememnt id not allowed
            self.ft_.sudo().unlink()
            self.mergeft_.statementid = statementid1
            
            if self.mergeft_.state == 'd':
                self.mergeft_.submit()
                
            for a in self.mergeft_.accline_s:
                a._docdate()

        return { 'type': 'ir.actions.act_view_reload' }

    
class Fthelperlines(models.TransientModel):
    _name = 'simrp.tfundsubmitline'

    fts_ = fields.Many2one( 'simrp.tfundsubmit', 'FTS' )
    agstaccline_ = fields.Many2one( 'simrp.accline', 'Agst Tx reference', required = True )
    docdate = fields.Date( 'Doc date', readonly = True )

    origAmount = fields.Float( 'Ref. Amt', digits=(8,2), readonly = True )
    adjAmount = fields.Float( 'Adj. Amt', digits=(8,2) )
    check = fields.Boolean(default=False )

    _order = 'docdate asc'
    
    @api.onchange('check')
    def checkon( self ):
        if self.check:
            um = self.fts_.amount
            for b in self.fts_.ref_s:
                if b.check:
                    um = um + b.adjAmount

            if um + self.origAmount > 0:
                self.adjAmount = self.origAmount
            else:
                self.adjAmount = -um
        else:
            self.adjAmount = 0
            
class Indirectexpense(models.Model):
    _name = 'simrp.indirectexpense'
    
    name = fields.Char( 'Transaction Code', size = 50, readonly = True, default="<draft>" )
    tdate = fields.Date( 'Entry Date', default=lambda self: fields.Date.today(), readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Party Account', required = True )
    #fundaccount_ = fields.Many2one( 'simrp.account', 'Fund Account (Payment done)' )
    expenseaccount_ = fields.Many2one( 'simrp.account', 'Expenditure A/c', required = True )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax scheme', required = True )

    docno = fields.Char( 'Invoice No.', size = 20, required=True )
    docdate = fields.Date( 'Invoice Date', default=lambda self: fields.Date.today(), required=True )
    
    des = fields.Char( 'Description', size = 200 )
    basicamount = fields.Float( 'Amount', digits=(8,2))
    duedate = fields.Date( 'Due Date', readonly = True, default=lambda self: fields.Date.today() )
    
    accline_s = fields.One2many( 'simrp.accline', 'indirectexpense_', 'Acc lines', readonly = True )
    indirectexpdeatil_s = fields.One2many( 'simrp.indirectexpensedetail', 'indirectexpense_', 'Indirect Expense' )
    
    tdsapply = fields.Boolean( 'Apply TDS?', default=False )
    tdsaccount_ = fields.Many2one( 'simrp.account', 'TDS Account' )
    tdsamount = fields.Float( 'Tds Amount', digits=(8,2), compute='_tdsamount', store=True )
    taxamount = fields.Float( 'Tax Amount', digits=(8,2), compute='_taxamount', store=True )
    netamount = fields.Float( 'Net Amount', digits=(8,2), compute='_netamount', store=True )
    payamount = fields.Float( 'Pay Amount', digits=(8,2), compute='_payamount', store=True )
    basicamount1 = fields.Float( 'Basic Amount', digits=(8,2), compute='_basicamount' )
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 's', 'Submit' ),
            ( 'a', 'Accepted' ),
            ], 'State', readonly = True, default='d' )

    gadjreason = fields.Text( 'GSTR2 Adj. Reason' )
    gstr2state  = fields.Selection( [
            ( 'na', 'Not Applicable' ),
            ( 'n', 'Not Matched' ),
            ( 'a', 'Auto Matched' ),
            ( 'm', 'Manual Decision' ),
            ], 'GSTR2 Status', readonly = True, default='n' )

    _order = "docdate desc"
    _sql_constraints = [ ('unique_dd1', 'unique (party_, docno, docdate)', 'Expense Document already exists!') ]
            
    @api.multi
    def gstr2manual(self):
        for o in self:
            if o.gadjreason:
                o.gstr2state = 'm'
            else:
                raise exceptions.UserError('Update GSTR2 Adjustment Reason')
                
    @api.multi
    @api.depends( 'indirectexpdeatil_s','indirectexpdeatil_s.qty','indirectexpdeatil_s.rate' )
    def _basicamount(self):
      for rec in self:
        amt = 0
        for o in rec.indirectexpdeatil_s:
            amt = amt + ( o.rate * o.qty )
        rec.basicamount1 = amt
           
    @api.multi
    @api.depends( 'tdsapply', 'party_', 'indirectexpdeatil_s','indirectexpdeatil_s.qty','indirectexpdeatil_s.rate' )
    def _tdsamount(self):
        for o in self:
            tds = 0
            if o.tdsapply:
                tds = o.basicamount1 * o.party_.getTdsRate()
            o.tdsamount = tds

    @api.multi
    @api.depends( 'basicamount1', 'taxscheme_' )
    def _taxamount(self):
        for o in self:
            o.taxamount = o.taxscheme_.compute( self.basicamount1 )[ 'tax' ]

    @api.multi
    @api.depends( 'basicamount1', 'taxamount' )
    def _netamount(self):
        for o in self:
            o.netamount = o.basicamount1 + o.taxamount

    @api.multi
    @api.depends( 'netamount', 'tdsamount' )
    def _payamount(self):
        for o in self:
            o.payamount = o.netamount - o.tdsamount
        
    @api.model
    def create(self, vals):
#        if vals[ 'basicamount1' ] <= 0:
#            raise exceptions.UserError('Check Amount')
        if vals[ 'tdsapply' ] == True:
            if not 'tdsaccount_' in vals.keys():
                raise exceptions.UserError('TDS Account Required')
            if not vals[ 'tdsaccount_' ]:
                raise exceptions.UserError('TDS Account Required')
        o = super(Indirectexpense, self).create(vals)
        _logger.info( str( vals ) )
        if o.tdsamount > 0:
            if not o.party_.account_.panno:
                raise exceptions.UserError('Party PAN Information for TDS missing')
        if o.taxscheme_.gstcheck:
            if not o.party_.account_.gstno:
                raise exceptions.UserError('Party GST Information missing')
        #if not o.fundaccount_:
        dd = o.party_.creditperiod
        o.duedate = o.tdate + relativedelta(days=+dd)
        return o
        
    @api.multi
    def accept(self):
        self.name = self.env['ir.sequence'].next_by_code('simrp.indirectexpense') + '-' + self.docno
        self.env[ 'simrp.accentry' ].browse( 1 ).initIEX( self.id, self.party_.account_, False, self.expenseaccount_, self.basicamount1, self.tdsamount, self.payamount, self.tdsaccount_, self.taxscheme_ )
        self.state = 'a'
        if not self.taxscheme_.gstcheck:
            self.gstr2state = 'na'
        return True

    @api.multi
    def submit(self):
        if self.basicamount1  <= 0:
            raise exceptions.UserError('Check Amount')
        self.name = self.env['ir.sequence'].next_by_code('simrp.purchasedraft') + '-' + self.docno
        self.state = 's'
        return True

    @api.multi
    def rework(self):
        self.state = 'd'
        return True

    @api.multi
    def update_exp(self):
        dr = self.env['simrp.indirectexpense'].search( [ ( 'state','=',['a','d','s'] ),( 'basicamount','!=',0 ) ])
        _logger.info( "#################################################." + str( dr ))
        a = 1
        for d in dr:
            des1 = d.des
            if not des1:
                des1 = "No Description (old system)"
            self.env[ 'simrp.indirectexpensedetail' ].create( {
                'indirectexpense_': d.id,
                'description': des1,
                'qty': a,
                'rate': d.basicamount,
                } )
        return True


    @api.multi
    def delete( self ):
        for o in self:
            for a in o.accline_s:
                a.delete()
            for d in o.indirectexpdeatil_s:
                d.unlink()
            o.unlink()
        return { 'type': 'ir.actions.act_view_reload' }

class Jtransaction(models.Model):
    _name = 'simrp.jtransaction'
    
    name = fields.Char( 'Transaction Code', size = 20, readonly = True )
    jdate = fields.Date( 'Journal date', default=lambda self: fields.Date.today() )
    draccount_ = fields.Many2one( 'simrp.account', 'Dr Account' )
    craccount_ = fields.Many2one( 'simrp.account', 'Cr Account' )
    des = fields.Text( 'Description', required = True )
    amount = fields.Float( 'Amount', digits=(8,2) )
    jamount = fields.Float( 'J.Amount', digits=(8,2), compute='_jamount', store=True )
    
    accline_s = fields.One2many( 'simrp.accline', 'jtransaction_', 'Acc lines' )
    
    def _jamount( self ):
        for o in self:
            a = 0
            for line in o.accline_s:
                a = a + line.amountdr
            o.jamount = a
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.jtransaction')
        # drtype = self.env[ 'simrp.account' ].browse( vals[ 'draccount_' ] ).type
        # crtype = self.env[ 'simrp.account' ].browse( vals[ 'craccount_' ] ).type
        # if drtype == 'fund':
            # if crtype != 'fund':
                # raise exceptions.UserError('Funds JV Contra invalid. Check accounts. Fund Account only')
        # if crtype == 'fund':
            # if drtype != 'fund':
                # raise exceptions.UserError('Funds JV Contra invalid. Check accounts. Fund Account only')
        o = super().create(vals)
        return o
    
    def addline( self ):
        o = self
        if self.amount <= 0:
            raise exceptions.UserError( 'Amount should be > 0' )
        self.env[ 'simrp.accentry' ].browse( 1 ).initJV( o.id, o.draccount_, o.craccount_, o.amount )
        o.draccount_ = False
        o.craccount_ = False
        o._jamount()

    def reset( self ):
        for a in self.accline_s:
            a.unlink()
        self._jamount()

class Indirectexpensedetail(models.Model):
    _name = 'simrp.indirectexpensedetail'

    indirectexpense_ = fields.Many2one( 'simrp.indirectexpense', 'Indirect Expense', required = True )
    description = fields.Text( 'Description', required = True )
    qty = fields.Float( 'Quantity', default=0, required = True )
    rate = fields.Float( 'Rate', default=0, required = True )
    amount = fields.Float( 'Amount', digits=(8,2), compute="_amt",store = True )

    @api.multi
    @api.depends('qty','rate')
    def _amt(self):
        for o in self:
            o.amount = o.qty * o.rate
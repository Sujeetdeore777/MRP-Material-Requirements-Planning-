# -*- coding: utf-8 -*-

import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import shiftinfo

import base64
# from OpenSSL.crypto import load_pkcs12
# from endesive import pdf


class Purchase(models.Model):
    _name = 'simrp.purchase'                                                                                        # simrp.indirectexpense

    name = fields.Char( 'Purchase Code.', size = 50, readonly = True )                                              #
    docno = fields.Char( 'Invoice No.', size = 50, required = True )                                                #
    docdate = fields.Date( 'Invoice Date', default=lambda self: fields.Date.today(), required = True )              #
    pdate = fields.Date( 'Purchase Entry Date', readonly = True, default=lambda self: fields.Date.today() )         # tdate
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )                                             #
    
    accline_s = fields.One2many( 'simrp.accline', 'purchase_', 'Account Postings', readonly = True )
    grn_s = fields.One2many( 'simrp.grn', 'purchase_', 'GRNs in this Invoice' )
    advancegrn_s = fields.One2many( 'simrp.advancegrn', 'purchase_', 'Misc. GRN' )
    directpurchase_s = fields.One2many( 'simrp.directpurchase', 'purchase_', 'Expenses' )
    adj = fields.Boolean( 'Manual Adjustments', default=False )
                                                                                # tdsapply = fields.Boolean( 'Apply TDS?', default=False )
    tdsaccount_ = fields.Many2one( 'simrp.account', 'TDS Account', readonly = True )
                                                                                # tdsadj = fields.Float( 'Tds Adjustment', digits=(8,2), default=0 )
                                                                                # autotdsamount = fields.Float( 'Calc. Tds', digits=(8,2), compute='_autotdsamount' )
    
    bataxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax (Adj)' ) 
    basicamountadj = fields.Float( 'Basic Adjustment', default=0 )
    adjreason = fields.Text( 'Adjustment Reason' )

    matchnet = fields.Float( 'Party Doc Value', digits=(8,2) )
    
    basicamount = fields.Float( 'Basic Amount', digits=(8,2), compute='_basicamount' )
    # tdsamount = fields.Float( 'Tds Amount', digits=(8,2), compute='_tdsamount' )
    tdsamount = fields.Float( 'Tds Amount', digits=(8,2), readonly = True )
    associate = fields.Selection( related='party_.associate' )
    
    taxamount = fields.Float( 'Tax Amount', digits=(8,2), compute='_taxamount' )
    netamount = fields.Float( 'Net Amount', digits=(8,2), compute='_netamount' )
    duedate = fields.Date( 'Due Date', readonly = True )
    
    regulergrn_amt = fields.Float( 'Regular Amount', digits=(8,2), compute='_regularamount' )
    directtool_amt = fields.Float( 'Misc Amount', digits=(8,2), compute='_directtoolamount' )
    directpur_amt = fields.Float( 'Expenses', digits=(8,2), compute='_directpuramount' )
    
    gadjreason = fields.Text( 'GSTR2 Adjustment Reason' )
    gstr2state  = fields.Selection( [
            ( 'na', 'Not Applicable' ),
            ( 'n', 'Not Matched' ),
            ( 'a', 'Auto Matched' ),
            ( 'm', 'Manual Decision' ),
            ( 'x', 'Mismatch' ),
            ], 'GSTR2 Status', readonly = True, default='n' )
            
    state = fields.Selection( [
            ( 'i', 'Init' ),
            ( 'd', 'Draft' ),
            ( 's', 'Submit' ),
            ( 'a', 'Accepted' ),
            ], 'State', readonly = True, default='i' )
    log = fields.Text( 'Log', readonly=True, default="" )

    _order = "docdate desc"
    _sql_constraints = [ ('unique_dd', 'unique (party_, docno, docdate)', 'Purchase Document already exists!') ]

    @api.onchange('party_')
    def party__change(self):
        dd = self.party_.creditperiod
        self.duedate = self.pdate + relativedelta(days=+dd)
#        self.write( { 'grn_s': [] } )                                                                              TODO UNLINK LOGIC, otherwise GRNs will be deleted
#        for g in self.grn_s:
#            sql = "update simrp_grn set purchase_=NULL where id=" + str(g.id)
#            self.env.cr.execute(sql)

    @api.onchange('adj')
    def adj_change(self):
        if self.adj == False:
            self.basicamountadj = 0
            # self.tdsadj = 0

    # @api.onchange('tdsapply')
    # def tdsapply_change(self):
        # if self.tdsapply == False:
            # self.tdsadj = 0
            
    @api.multi
    @api.depends( 'grn_s', 'basicamountadj', 'adj','advancegrn_s','directpurchase_s' )
    def _basicamount(self):
        for o in self:
            ba_grn = 0
            ba_agrn = 0
            ba_dpur = 0
            if o.adj:
                ba_grn = o.basicamountadj
            for g in o.grn_s:
                ba_grn = ba_grn + ( g.basicamount )
            for g in o.advancegrn_s:
                ba_agrn = ba_agrn + ( g.amount )
            for g in o.directpurchase_s:
                ba_dpur = ba_dpur + ( g.amount )
            o.basicamount = ba_grn + ba_agrn + ba_dpur

    @api.multi
    @api.depends( 'grn_s')
    def _regularamount(self):
        for o in self:
            ba_grn = 0
            for g in o.grn_s:
                ba_grn = ba_grn + ( g.basicamount )
            o.regulergrn_amt = ba_grn 

    @api.multi
    @api.depends( 'advancegrn_s' )
    def _directtoolamount(self):
        for o in self:
            ba_agrn = 0
            for g in o.advancegrn_s:
                ba_agrn = ba_agrn + ( g.amount )
            o.directtool_amt = ba_agrn

    @api.multi
    @api.depends( 'directpurchase_s' )
    def _directpuramount(self):
        for o in self:
            ba_dpur = 0
            for g in o.directpurchase_s:
                ba_dpur = ba_dpur + ( g.amount )
            o.directpur_amt = ba_dpur

    # @api.multi
    # @api.depends( 'grn_s', 'adj', 'basicamountadj', 'tdsapply','advancegrn_s','directpurchase_s' )
    # def _autotdsamount(self):
        # for o in self:
            # tds = 0
            # if o.tdsapply:
                # tds = o.basicamount * o.party_.getTdsRate()
            # o.autotdsamount = tds
            
    # @api.multi
    # @api.depends( 'grn_s', 'adj', 'basicamountadj', 'tdsapply', 'tdsadj' )
    # def _tdsamount(self):
        # for o in self:
            # tds = 0
            # if o.tdsapply:
                # tds = o.basicamount * o.party_.getTdsRate()
                # tds = tds + o.tdsadj
            # o.tdsamount = tds

    @api.multi
    @api.depends( 'grn_s', 'basicamountadj', 'adj', 'bataxscheme_', 'grn_s', 'basicamountadj', 'adj','advancegrn_s' )
    def _taxamount(self):
        for o in self:
            #taxb = self.env[ 'simrp.account' ].search( [ ( 'type', '=', 'tax' ) ] )
            #taxd = {}
            #for tax in taxb:
            #    taxd[ tax.id ] = 0
            t = 0
            for g in o.grn_s:
                t = t + g.taxscheme_.compute( g.basicamount )[ 'tax' ]
            for g in o.advancegrn_s:
                t = t + g.taxscheme_.compute( g.amount )[ 'tax' ]
            for g in o.directpurchase_s:
                t = t + g.taxscheme_.compute( g.amount )[ 'tax' ]
            if o.adj:
                if o.basicamountadj != 0:
                    t = t + o.bataxscheme_.compute( o.basicamountadj )[ 'tax' ]
            o.taxamount = t

    @api.multi
    @api.depends( 'grn_s', 'basicamountadj', 'adj', 'bataxscheme_', 'grn_s', 'basicamountadj', 'adj','advancegrn_s' )
    def _netamount(self):
        for o in self:
            o.netamount = o.basicamount + o.taxamount
            
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.purchasedraft') + '-' + vals[ 'docno' ]
        vals['log'] = shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] Draft created\r\n"
        return super(Purchase, self).create(vals)

    @api.one
    def gstr2manual(self):
        gl = self.env[ 'simrp.gstr2line' ].browse( self.env.context[ 'glid' ] )
        gl.match = 'a'
        self.gstr2state = 'm'
        self.gadjreason = "Manual match: " + str( gl.gstr2_.id ) + " / " + gl.invno + " / " + str( gl.totgst )
        #if o.gadjreason:
        #    o.gstr2state = 'm'
        #else:
        #    raise exceptions.UserError('Update Decision and debit details')

    @api.one
    def gstr2mismatch(self):
        gl = self.env[ 'simrp.gstr2line' ].browse( self.env.context[ 'glid' ] )
        gl.match = 'a'
        self.gstr2state = 'x'
        self.gadjreason = "Mismatch: " + str( gl.gstr2_.id ) + " / " + gl.invno + " / " + str( gl.totgst )

    @api.one
    def gstr2ok(self):
        if self.gadjreason:
            self.gstr2state = 'm'

    # def gstr2mismatchmark(self):
        # self.gstr2state = 'x'
        # self.gadjreason = "Mismatch: Missing"
                
    @api.multi
    def grnrate(self):
        for o in self:
            for g in o.grn_s:
                g.initRates()

    @api.multi
    def grnreset(self):
        for o in self:
            for g in o.grn_s:
                g.purchase_ = False
            
    @api.multi
    def submit(self):
        if self.netamount <= 0:
            raise exceptions.UserError('Net Amonut is 0')        
        if abs( self.netamount - self.matchnet ) > 0.75:
            raise exceptions.UserError('Calculated Net amt and Party Document Value not matching: ' + self.name)
        if self.tdsamount > 0:
            if self.party_.panno == "":
                raise exceptions.UserError('Party PAN Information for TDS missing')
        for g in self.grn_s:
            if g.taxscheme_.gstcheck:
                if self.party_.gstno == "":
                    raise exceptions.UserError('Party GST Information missing')
                if g.item_.hsnsac == '':
                    raise exceptions.UserError('Item HSN/SAC Information missing')
                if g.qcstate not in ['ok','dok','rej','na']:
                    raise exceptions.UserError('GRN QC Decision pending')
        for g in self.advancegrn_s:
            if g.taxscheme_.gstcheck:
                if self.party_.gstno == "":
                    raise exceptions.UserError('Party GST Information missing')
                if g.item_.hsnsac == '':
                    raise exceptions.UserError('Item HSN/SAC Information missing')
        if self.basicamountadj != 0:
            if not self.bataxscheme_:
                raise exceptions.UserError('Adjustment amount tax scheme not provided')
            if self.bataxscheme_.gstcheck:
                if self.party_.gstno == "":
                    raise exceptions.UserError('Party GST Information missing')
        if self.party_.tdsdeduct:
            #search and set tdsaccount, else raise error
            #calc self.tdsamount
            tdsacs = self.env[ 'simrp.account' ].search( [ ( 'type', '=', 'tds' ), ( 'code','=',self.party_.associate ) ] )
            if not tdsacs:
                raise exceptions.UserError( 'TDS Account and Autocode not defined: ' + self.party_.associate )
            self.tdsaccount_ = tdsacs[ 0 ]
            self.tdsamount = self.basicamount * self.tdsaccount_.opbal / 100
            
        
        self.state = 's'
        if not self.log:
            self.log = ""
        self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] Submit\r\n"
        
        if self.checkAutoAccept():
            self.accept()
            self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] Auto Accept Process\r\n"
        return True

    @api.model
    def checkAutoAccept( self ):
        r = True
        if ( ( self.directtool_amt > 0 ) or
           ( self.directpur_amt > 0 ) or
           ( self.adj == True ) ):
            r = False
        for g in self.grn_s:
            if g.rejinqty > 0:
                r = False
            if g.recdate.date() > self.docdate:
                r = False
                self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] GRN Date Check\r\n"
        return r
        
    @api.multi
    def draft(self):
        self.state = 'd'
        if not self.log:
            self.log = ""
        self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] Set to Draft\r\n"
        return True
    
    @api.multi
    def draft1(self):
        for o in self.accline_s:
            for r in o.refadjo_s:
                r.unlink()
            for r in o.refadj_s:
                r.unlink()
            o.unlink()
        self.state = 's'
        if not self.log:
            self.log = ""
        self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] Entry Reset\r\n"
        return True

    def repost(self):
        # raise exceptions.UserError('IN ACTION')
        # if not self.env['res.users'].has_group('simrp.group_simrp_ceo'):
            # raise exceptions.UserError('You do not have permission to use this action')
        for o in self:
            o.draft1()
            o.draft()
            o.submit()
            if o.state != 'a':
                o.accept()
        return True

    @api.multi
    def accept(self):
        if abs( self.netamount - self.matchnet ) > 0.75:
            raise exceptions.UserError('Calculated Net amt and Party Document Value not matching: ' + self.name )
        if not self.log:
            self.log = ""
    
        # taxb = self.env[ 'simrp.account' ].search( [ ( 'type', '=', 'tax' ) ] )
        taxd = {}
        # for tax in taxb:
            # taxd[ tax.id ] = 0
        # purb = self.env[ 'simrp.account' ].search( [ ( 'type', '=', 'purc' ) ] )
        purd = {}
        # for pur in purb:
            # purd[ pur.id ] = 0

        gstp = 0
        for g in self.grn_s:
            if g.taxscheme_.gstcheck:
                gstp = 1
            ba = g.basicamount
            t = g.taxscheme_.compute( ba )
            # _logger.info( '######################################## ' + str( g.id ) )
            
            if g.taxscheme_.account_.id not in purd:
                purd[ g.taxscheme_.account_.id ] = 0            
            purd[ g.taxscheme_.account_.id ] += ( t[ 'ba1' ] )
            
            if t[ 'ba2' ] > 0:
                if g.taxscheme_.account2_.id not in purd:
                    purd[ g.taxscheme_.account2_.id ] = 0            
            
                purd[ g.taxscheme_.account2_.id ] += ( t[ 'ba2' ] )
            for taxline in t[ 'printTaxes' ]:
                if taxline[ 'taxaccountid' ] not in taxd:
                    taxd[ taxline[ 'taxaccountid' ] ] = 0
                taxd[ taxline[ 'taxaccountid' ] ] += taxline[ 'taxamount' ]
                
        for g in self.advancegrn_s:
            if g.taxscheme_.gstcheck:
                gstp = 1
            ba = g.amount
            t = g.taxscheme_.compute( ba )

            if g.taxscheme_.account_.id not in purd:
                purd[ g.taxscheme_.account_.id ] = 0            
            purd[ g.taxscheme_.account_.id ] += ( t[ 'ba1' ] )
            if t[ 'ba2' ] > 0:
                if g.taxscheme_.account2_.id not in purd:
                    purd[ g.taxscheme_.account2_.id ] = 0            
            
                purd[ g.taxscheme_.account2_.id ] += ( t[ 'ba2' ] )
            for taxline in t[ 'printTaxes' ]:
                if taxline[ 'taxaccountid' ] not in taxd:
                    taxd[ taxline[ 'taxaccountid' ] ] = 0
                taxd[ taxline[ 'taxaccountid' ] ] += taxline[ 'taxamount' ]
        for g in self.directpurchase_s:
            if g.taxscheme_.gstcheck:
                gstp = 1
            ba = g.amount
            t = g.taxscheme_.compute( ba )
            if g.expenseaccount_.id not in purd:
                purd[ g.expenseaccount_.id ] = 0            
            purd[ g.expenseaccount_.id ] += ( t[ 'ba1' ] )
            # if g.taxscheme_.account_.id not in purd:
                # purd[ g.taxscheme_.account_.id ] = 0            
            # purd[ g.taxscheme_.account_.id ] += ( t[ 'ba1' ] )
            # if t[ 'ba2' ] > 0:
                # if g.taxscheme_.account2_.id not in purd:
                    # purd[ g.taxscheme_.account2_.id ] = 0            
                # purd[ g.taxscheme_.account2_.id ] += ( t[ 'ba2' ] )

            for taxline in t[ 'printTaxes' ]:
                if taxline[ 'taxaccountid' ] not in taxd:
                    taxd[ taxline[ 'taxaccountid' ] ] = 0
                taxd[ taxline[ 'taxaccountid' ] ] += taxline[ 'taxamount' ]

        if self.adj:
            if self.basicamountadj != 0:
                t = self.bataxscheme_.compute( self.basicamountadj )
                if self.bataxscheme_.account_.id not in purd:
                    purd[ self.bataxscheme_.account_.id ] = 0            
                purd[ self.bataxscheme_.account_.id ] += ( t[ 'ba1' ] )
                if t[ 'ba2' ] > 0:
                    if self.bataxscheme_.account2_.id not in purd:
                        purd[ self.bataxscheme_.account2_.id ] = 0            
                    purd[ self.bataxscheme_.account2_.id ] += ( t[ 'ba2' ] )
                for taxline in t[ 'printTaxes' ]:
                    if taxline[ 'taxaccountid' ] not in taxd:
                        taxd[ taxline[ 'taxaccountid' ] ] = 0
                    taxd[ taxline[ 'taxaccountid' ] ] += taxline[ 'taxamount' ]
        # for k in list( purd ):
            # if purd[ k ] == 0:
                # del purd[ k ]
        # for k in list( taxd ):
            # if taxd[ k ] == 0:
                # del taxd[ k ]
        
        dd = self.party_.creditperiod
        self.duedate = self.pdate + relativedelta(days=+dd)
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> basicamount " + str( self.basicamount ) )
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   netamount " + str( self.netamount ) )
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   tdsamount " + str( self.tdsamount ) )
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>        purd " + str( purd ) )
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>        taxd " + str( taxd ) )
        
        self.env[ 'simrp.accentry' ].browse( 1 ).initPurchase( self.id, self.party_.account_, self.basicamount, self.netamount, self.tdsamount, self.tdsaccount_, taxd, purd )
        self.state = 'a'
        if not ( self.name.startswith( 'PUR' ) or self.name.startswith( 'IExp' ) ):
            self.name = self.env['ir.sequence'].next_by_code('simrp.purchase') + '-' + self.docno
        self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + " [" + self.env.user.name + "] Accepted\r\n"
        
        if gstp == 0:
            self.gstr2state = 'na'

        for g in self.grn_s:
            g.accstate = 'i'
            g.checkClose()
        
        for g in self.advancegrn_s:
            g.state = 'acc'

        self.env[ 'simrp.auditlog' ].log( self, 'Purchase: ', self.read( self.logfields )[0], False, False )        
        return True

    logfields = [ 'name', 'party_', 'docno', 'docdate', 'adj', 'basicamountadj', 'regulergrn_amt', 'directtool_amt', 'directpur_amt', 'netamount'  ]
    
class Debit(models.Model):
    _name = 'simrp.debit'
    
    name = fields.Char( 'Debit Note No.', size = 20, readonly = True )

    qcinspection_ = fields.Many2one( 'simrp.qcinspection', 'Qcinspection', readonly = True )

    rdate = fields.Date( 'Debit Date', default=lambda self: fields.Date.today())
    party_ = fields.Many2one( 'simrp.party', 'Party' )    
    ar = fields.Text( 'Remarks' )
    basicamount = fields.Float( 'Basic Amount', digits=(8,2), default=0 )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme' ) 

    dndelivery = fields.Char( 'Delivery Document Ack', size = 200, default="" )
    returntransport = fields.Char( 'Return transport details', size = 200, default="" )

    netamount = fields.Float( 'Net Amount', digits=(8,2), readonly = True )

    group = fields.Selection( [
            ( 's', 'S' ),
            ( 'v', 'V' ),
            ], 'Group', default='s' )

    gstreturn = fields.Selection( [
            ( '1', 'GSTR1 Sales Impact' ),
            ( '3', 'GSTR3 Purchase Impact' ),
            ( '0', 'Non GST' ),
            ], 'Gst Return Impact', default='1' )

    state = fields.Selection( [
            ( 'p', 'Pending' ),
            ( 'a', 'Accounted' ),
            ( 'dc', 'DC Prepared' ),
            ( 'ack', 'Acknowledged & Closed' ),
            ( 'mna', 'Closed w/o Material Movement' ),
            ], 'Status', readonly = True, default='p' )

    stock_ = fields.Many2one( 'simrp.stock', 'Material Return entry', readonly = True )
    accline_s = fields.One2many( 'simrp.accline', 'debit_', 'Account Postings' )

    filename1 = fields.Char( 'FNM', compute='_signinv' )
    file1 = fields.Binary( 'FL1', compute='_signinv' )
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.debit')
        return super(Debit, self).create(vals)

    @api.multi
    def post( self ):
        if self.basicamount == 0:
            raise exceptions.UserError('Enter Basic Amount and Tax Scheme')
        if not self.taxscheme_:
            raise exceptions.UserError('Enter Basic Amount and Tax Scheme')
        self.netamount = self.env[ 'simrp.accentry' ].browse( 1 ).initDN( 
                            self.id, self.party_.account_, 
                            self.basicamount,
                            self.taxscheme_ )
        self.state = 'a'
        return True

    def redraft( self ):
        for al in self.accline_s:
            al.delete()
        self.state = 'p'
        
    @api.multi
    def ack( self ):
        if self.returntransport == "":
            raise exceptions.UserError('Enter Ack details first')
        self.state = 'ack'
        return True

    @api.multi
    def close( self ):
        self.state = 'mna'
        return True


    @api.multi
    def prepareDC(self):
        if not self.qcinspection_:
            raise exceptions.UserError('This debit is not linked to QC Inspection')
        ref = '%s,%s' % ( 'simrp.debit', self.id )
        self.stock_ = self.env[ 'simrp.stock' ].create( {
            'ref': ref,
            'party_': self.party_.id,
            'item_': self.qcinspection_.item_.id,
            'rejoutqty': self.qcinspection_.rejqty
        } )
        self.state = 'dc'
        return True
        
    @api.multi
    def printDC(self):
        return self.env.ref('simrp.action_report_printdndc').report_action(self)
        return True

    @api.multi
    def printDCpdf(self):
        #return self.env.ref('simrp.action_report_printdndcpdf').report_action(self)
        return {
            'name': 'FEC',
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=simrp.debit&id={}&field=file1&filename_field=filename1&download=true'.format(
                self.id
            ),
            'target': 'new',
        }        
        

    def _signinv( self ):
        for o in self:
            o.filename1 = o.party_.vcode + '_' + o.name + '_' + o.rdate.strftime('%d%m%Y') + '.pdf'
            p = self.env.ref('simrp.action_report_printdndcpdf').render_qweb_pdf(res_ids=self.id)[0]
            
            _logger.info( p[0:1000] )
            
            bdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S+00'00'")
            dct = {
                b'sigflags': 3,
                b'sigpage': 1,
                b'sigbutton': True,
                b'contact': b'ks12mobile@gmail.com',
                b'location': b'India',
                b'signingdate': bdate.encode( 'utf-8' ),
                b'reason': b'Invoice Signature',
                b'signature': b'Kaushal Shah',
                b'signaturebox': (500, 0, 600, 100),
            }
                
            signfile = self.env['ir.config_parameter'].sudo().get_param('signfilewithpath')
            signpass = self.env['ir.config_parameter'].sudo().get_param('signfilepassword')
            p12 = load_pkcs12(open(signfile, 'rb').read(), signpass)
            
            ps = pdf.cms.sign( p, dct, p12.get_privatekey().to_cryptography_key(), p12.get_certificate().to_cryptography(), [], 'sha256' )
            
            o.file1 = base64.b64encode( p + ps )

    def delete( self ):
        for o in self:
            for a in o.accline_s:
                a.unlink()
            o.unlink()

class DirectPurchase(models.Model):
    _name = 'simrp.directpurchase'

    purchase_ = fields.Many2one( 'simrp.purchase', 'Purchase Entry:', required = True )
    date = fields.Date( 'Inw Date', default=lambda self: fields.Date.today(), required = True )
    des = fields.Char( 'Description', size = 400, required = True )
    qty = fields.Float( 'Quantity', default=0, digits=(8,2), required = True )
    rate = fields.Float( 'Rate', default=0, required = True )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax scheme', required = True )
    amount = fields.Float( 'Amount', digits=(8,2), compute="_amt",store = True )

    expenseaccount_ = fields.Many2one( 'simrp.account', 'Expenditure A/c', required = True )

    @api.multi
    @api.depends('qty','rate')
    def _amt(self):
        for o in self:
            o.amount = o.qty * o.rate


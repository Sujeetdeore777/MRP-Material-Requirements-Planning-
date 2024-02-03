# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from . import shiftinfo
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Grnmaster(models.Model):
    _name = 'simrp.grnmaster'
    
    name = fields.Char( 'Inward Code', size = 15, readonly = True )
    dcno = fields.Char( 'Party DC No.', size = 20, required = True )
    dcdate = fields.Date( 'DC Date', required = True, default=datetime.date.today() )

    party_ = fields.Many2one( 'simrp.party', 'Supplier', required = True )
    porder_s = fields.One2many( 'simrp.porder', 'party_', 'Open Purchase Orders', related='party_.porder_s' )
    subcondc_s = fields.One2many( 'simrp.subcondc', 'party_', 'Open Subcontracting DC', related='party_.subcondc_s' )

    grn_s = fields.One2many( 'simrp.grn', 'grnmaster_', 'GRNs', readonly = True )
    
    _sql_constraints = [
        ('dc_uniq', 'unique(party_,dcno,dcdate)', 'This DC is already booked!'),
    ]
    
    _order = "id desc"

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.grnmaster')
        return super(Grnmaster, self).create(vals)

class Grn(models.Model):
    _name = 'simrp.grn'
    # _inherits = {'simrp.stock': 'stock_'} 

    stock_ =  fields.Many2one( 'simrp.stock', 'Stock', readonly=True, ondelete="cascade")
    recdate = fields.Datetime( 'Time', readonly = True, default=lambda self: fields.Datetime.now() )
    party_ = fields.Many2one( 'simrp.party', 'Party' )
    item_ = fields.Many2one('simrp.item', 'Item' )
    itemtype = fields.Selection( related='item_.type', string='Item Type' )
    itemuom_ = fields.Many2one( related='item_.uom_' )     
    okinqty = fields.Float( 'Ok In', digits=(8,2), default=0 )
    rejinqty = fields.Float( 'Rej In', digits=(8,2), default=0 )
    okoutqty = fields.Float( 'Ok Out', digits=(8,2), default=0 )
    rejoutqty = fields.Float( 'Rej Out', digits=(8,2), default=0 )

    
    name = fields.Char( 'GRN Code', size = 50, readonly = True )
    hsnsac = fields.Char( related='stock_.item_.hsnsac' )
    
    grnmaster_ = fields.Many2one( 'simrp.grnmaster', 'Grnmaster', readonly = True )
    dcno = fields.Char( 'Doc No.', size = 20, related='grnmaster_.dcno' )
    dcdate = fields.Date( 'DC Date', related='grnmaster_.dcdate' )
    porder_ = fields.Many2one( 'simrp.porder', 'Porder', readonly = True )
    subcondc_ = fields.Many2one( 'simrp.subcondc', 'Subcon DC', readonly = True )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess', readonly = True )
    
    #party_ = fields.Many2one( 'simrp.party', 'Supplier', required = True )
    #item_ = fields.Many2one( 'simrp.item', 'Item', related='porder_.item_' )
    uom_ = fields.Many2one( 'simrp.uom', 'Base UOM', related='item_.uom_' ) 

    qtydc = fields.Float( 'DC Qty', digits=(8,2), readonly = True )
    qtyactual = fields.Float( 'GRN Qty', digits=(8,2), readonly = True )
    phycounter = fields.Char( 'Other Verification (Wt. or pc)', readonly = True )
    qtyremarks = fields.Text( 'Qtyremarks', readonly = True )

    qcstate = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'p', 'Inspection' ),
            ( 'i', 'Quality Issue' ),
            ( 'ok', 'Inspected OK' ),
            ( 'dok', 'Deviation / Sorting' ),
            ( 'rej', 'Lot Rejected' ),
            ( 'na', 'QC N/A' ),
            ], 'QC Status', readonly = True, default='d' )
    qcinspection_ = fields.Many2one( 'simrp.qcinspection', 'QC Inspection', readonly = True )
    qcidate = fields.Datetime( related='qcinspection_.idate' )
    qccdate = fields.Datetime( related='qcinspection_.cdate' )
    qclog = fields.Text( 'Log', related='qcinspection_.log' )
    
    accstate = fields.Selection( [
            ( 'u', 'Unaccounted' ),
            ( 'i', 'Invoiced' ),
            ( 'na', 'N/A' ),
            ], 'Accounting', readonly = True, default='u' )
    billconv = fields.Float( 'Billconv', digits=(8,2), readonly = True, default="1" )
    billqty = fields.Float( 'Billing qty', digits=(8,2), compute='_billqty' )
    rate = fields.Float('Rate / unit', readonly = True )
    loadrate = fields.Float('Load charges', readonly = True, default="0" )
    testrate = fields.Float('Test charges', readonly = True, default="0" )
    transportrate = fields.Float('Transport charges', readonly = True, default="0" )
    basicamount = fields.Float( 'BasicAmt', digits=(8,2), compute="_basicamount" )
    charges = fields.Float( 'Charges', digits=(8,2), compute="_charges" )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme', readonly = True ) 
    purchase_ = fields.Many2one( 'simrp.purchase', 'Purchase', readonly = True, ondelete='set null' )
            
    servicestate = fields.Selection( [
            ( 'p', 'Pending' ),
            ( 'a', 'Approved' ),
            ( 'x', 'No Billing' ),
            ( 'na', 'N/A' ),
            ], 'Svc Check', readonly = True, default='p' )
    serviceremarks = fields.Text( 'Service approval remarks', readonly = True )
            
    state = fields.Selection( [
            ( 'qtm', 'Qty Mismatch' ),
            ( 'p', 'InProcess' ),
            ( 'c', 'Closed' ),
            ], 'Status', readonly = True, default='qtm' )

    grnmodedc = fields.Selection( [
            ( 'o', 'Receivable Output Item' ),
            ( 'i', 'Input Item Return' ),
            ( 'b', 'Receivable Byproduct Item' ),
            ], 'DC GRN Item', default='o' )
    
    _order = 'recdate desc'
    #statetext = fields.Char( 'Statetext', compute='_statetext', store=False )
    #'qtyaccount': fields.float('Quantity Billed', digits = (8, 2),readonly=True, ),
    #'accountinfo': fields.text('Billing / Debit info', readonly=True, ),

    #@api.multi
    #@api.depends('qcstate','accstate','servicestate','grnstate')
    #def _statetext(self):
    #    for o in self:
    #        _logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + str( dict( self._fields[ 'qcstate' ].selection ) ) )
    #        o.statetext = dict( self._fields[ 'grnstate' ].selection )[ o.grnstate ] + " [QC]> " + dict( self._fields[ 'qcstate' ].selection )[ o.qcstate ] + " [SRV]> " + dict( #self._fields[ 'servicestate' ].selection )[ o.servicestate ] + " [AC]> " + dict( self._fields[ 'accstate' ].selection )[ o.accstate ]

    @api.multi
    def deletegrn( self ):
        for o in self:
            if o.accstate == 'i':
                raise exceptions.UserError('GRN already accounted. Cannot Delete')
            if o.qcinspection_:
                o.qcinspection_.deleteqci()
            if o.subcondc_:
                o.subcondc_.state = 'o'
            if o.porder_:
                o.porder_.reopen()
            if o.stock_:
                o.stock_.unlink()
            o.unlink()
        return { 'type': 'ir.actions.act_view_reload' }
                
    def resetinvoice( self ):
        for o in self:
            if ( ( o.accstate == 'i' ) and ( not o.purchase_ ) ):
                #reset GRN 
                o.accstate  = 'u'
            else:
                raise exceptions.UserError('Cannot reset GRN invoice state where Purchase Entry is linked.')

    @api.multi
    @api.depends('okinqty', 'billconv', 'rate', 'loadrate', 'testrate', 'transportrate' )
    def _basicamount( self ):
        for o in self:
            o.basicamount = ( o.billqty * o.rate ) + o.loadrate + o.testrate + o.transportrate

    @api.multi
    @api.depends('loadrate', 'testrate', 'transportrate' )
    def _charges( self ):
        for o in self:
            o.charges = o.loadrate + o.testrate + o.transportrate
    
    @api.multi
    @api.depends('okinqty', 'billconv')
    def _billqty(self):
        for o in self:
            o.billqty = o.okinqty / o.billconv
                    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.grn')
        if vals['qtyactual'] == vals['qtydc']:
            vals['state'] = 'p'
            vals['okinqty'] = vals['qtyactual']
            #vals['qtyremarks'] = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT) + " Qty OK\r\n"
            vals['qtyremarks'] = shiftinfo.getnowlocaltimestring( self ) + " Qty OK\r\n"
        else:
            vals['state'] = 'qtm'
            #vals['qtyremarks'] = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT) + " Qty Mismatch - DC: " + str(vals['qtydc']) + " Actual: " + str(vals['qtyactual']) + "\r\n"
            vals['qtyremarks'] = shiftinfo.getnowlocaltimestring( self ) + " Qty Mismatch - DC: " + str(vals['qtydc']) + " Actual: " + str(vals['qtyactual']) + "\r\n"
        return super(Grn, self).create(vals)

    @api.model
    def initRates(self):
        if self.porder_:
            self.rate = self.porder_.rate
            self.loadrate = self.porder_.loadrate
            self.testrate = self.porder_.testrate
            self.transportrate = self.porder_.transportrate
            self.taxscheme_ = self.porder_.taxscheme_.id
        else:
            #subcondc
            if self.grnmodedc == 'o':
                self.rate = self.subcondc_.processsubcon_.rate
                self.taxscheme_ = self.subcondc_.processsubcon_.taxscheme_.id
                # _logger.info( str( self.id ) + ' GRN tx sch id: ' + str( self.subcondc_.processsubcon_.taxscheme_.id ) )

        
    def initGRN(self):
        ite_ = False
        
        if self.porder_:
            ite_ = self.porder_.item_
            self.itemprocess_ = self.porder_.itemprocess_.id
        else:
            #subcondc
            if self.grnmodedc == 'o':
                ite_ = self.subcondc_.outputitem_
            elif self.grnmodedc == 'i':
                ite_ = self.subcondc_.item_
                self.accstate = 'na'
            elif self.grnmodedc == 'b':
                ite_ = self.subcondc_.byproductitem_            
                self.accstate = 'na'
            self.itemprocess_ = self.subcondc_.itemprocess_.id

        self.item_ = ite_.id
        self.initRates()
        if self.porder_:
            if not self.stock_:
                stk = self.env[ 'simrp.stock' ].create( {} )
                stk.initStock( ite_, 'simrp.grn', self.id, self.grnmaster_.party_ )
                self.stock_ = stk.id
        
        type = self.itemtype
        if type in [ 'service' ]:
            #service po -> srn > approval > accounts					(Expense Head)
            self.qcstate = 'na'
            self.servicestate = 'p'
            self.serviceremarks = shiftinfo.getnowlocaltimestring( self ) + " [Service GRN] Approval Requested\r\n"
        else:
            self.servicestate = 'na'
            self.serviceremarks = shiftinfo.getnowlocaltimestring( self ) + " Service Approval NA\r\n"

        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " + self.state )
        if self.state == 'p':
            #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " + type )
            #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " + self.grnmodedc )
            if ( type in [ 'rmb', 'bo', 'fg' ] ) and self.grnmodedc == 'o':
            #if ( type in [ 'rmb', 'bo' ] ) and self.grnmodedc == 'o':
                #controlled material -> grn > qty > stock > accounts > qc > stock > accounts	(Item - Process)
                self.qcinspection_ = self.env['simrp.qcinspection'].create( { 
                                'grn_': self.id, 
                                'item_': self.item_.id, 
                                'itemprocess_': self.itemprocess_.id, 
                                'lotqty': self.qtyactual,
                                'log': 'GRN Auto QC Init: GMT ' + datetime.datetime.now().strftime( DEFAULT_SERVER_DATETIME_FORMAT ) + '\n'
                                } )
                self.qcinspection_.initQCI()
                self.qcstate = 'p'
            else:
                #direct use material -> grn > qty > stock > accounts		(Item)
                self.qcstate = 'na'
                self.rejinqty = 0
        
        self.checkClose()
        if self.state == 'qtm':
            self.env[ 'simrp.auditlog' ].log( self, self.logstring(), {}, False, False )                
        return True

    def logstring( self ):
        _logger.info( self.party_.name )
        _logger.info( self.name )
        _logger.info( self.item_.name )
        _logger.info( self.dcno )
        
        return self.name + '/' + self.dcno + ' ' + self.party_.name + ' ' + self.item_.name + ' [' + str( self.qtydc ) + ' / ' + str( self.qtyactual ) + '] ' + self.phycounter

    @api.multi
    def checkClose( self ):
        if ( ( self.servicestate in ['a','x','na'] ) and ( self.qcstate in ['ok','dok','rej','na'] ) ) and ( self.accstate in ['i','na'] ):
            self.state = 'c'
        if self.porder_:
            self.stock_.okinqty = self.okinqty
            self.stock_.rejinqty = self.rejinqty
    
    @api.multi
    def update(self, qa, ar, f):
        self.qtyactual = qa
        self.qtyremarks = self.qtyremarks + shiftinfo.getnowlocaltimestring( self ) + " " + ar + "\r\n"
        if f:
            self.state = 'p'
            self.okinqty = qa
            self.initGRN()
        return True

    @api.multi
    def approveservice(self, ar):
        self.serviceremarks = self.serviceremarks + shiftinfo.getnowlocaltimestring( self ) + " " + ar + "\r\n"
        self.servicestate = 'a'
        return True
    @api.multi
    def notapproveservice(self, ar):
        self.serviceremarks = self.serviceremarks + shiftinfo.getnowlocaltimestring( self ) + " " + ar + "\r\n"
        self.servicestate = 'x'
        return True
    @api.multi
    def updateservice(self, ar):
        self.serviceremarks = self.serviceremarks + shiftinfo.getnowlocaltimestring( self ) + " " + ar + "\r\n"
        return True
    @api.multi
    def resetservice(self, ar):
        self.serviceremarks = self.serviceremarks + shiftinfo.getnowlocaltimestring( self ) + " Service decision reset\r\n"
        self.servicestate = 'p'        
        return True

class Tgrn(models.TransientModel):
    _name = 'simrp.tgrn'

    grnmaster_ = fields.Many2one( 'simrp.grnmaster', 'Grnmaster', readonly = True )
    porder_ = fields.Many2one( 'simrp.porder', 'Porder', readonly = True )
    subcondc_ = fields.Many2one( 'simrp.subcondc', 'Subcon DC', readonly = True )
    dcno = fields.Char( 'Party DC No.', size = 20, related='grnmaster_.dcno' )
    poqty = fields.Float( 'PO Qty', related='porder_.poqty' )
    balanceqty = fields.Float( 'Balance Qty', related='porder_.balanceqty' )
    item_ = fields.Many2one( 'simrp.item', 'Item', related='porder_.item_' )

    itemdco_ = fields.Many2one( 'simrp.item', 'Subcon Output Item', related='subcondc_.outputitem_' )
    itemdci_ = fields.Many2one( 'simrp.item', 'Subcon Input Item', related='subcondc_.item_' )
    itemdcb_ = fields.Many2one( 'simrp.item', 'Subcon By-product Item', related='subcondc_.byproductitem_' )
    balanceqtydco = fields.Float( 'Balance DC Output Qty', related='subcondc_.balanceqtyo', digits=(8,2) )
    balanceqtydci = fields.Float( 'Balance DC Input Qty', related='subcondc_.balanceqtyi', digits=(8,2) )
    balanceqtydcb = fields.Float( 'Balance DC By-product Qty', related='subcondc_.balanceqtyb', digits=(8,2) )
    balanceqtydcoruom = fields.Float( related='subcondc_.balanceqtyoruom', digits=(8,2) )

    itemuom_ = fields.Many2one( related='item_.uom_' )

    rateuom_ = fields.Many2one( 'simrp.uom', 'Party UOM', related='subcondc_.rateuom_' )
    itemouom_ = fields.Many2one( related='subcondc_.outputitem_.uom_' )
    itemiuom_ = fields.Many2one( related='subcondc_.item_.uom_' )
    itembuom_ = fields.Many2one( related='subcondc_.byproductitem_.uom_' )
    
    qtydc = fields.Float( 'DC Quantity', digits=(8,2), required = True )
    qtyactual = fields.Float( 'Physical Qty baseUOM', digits=(8,2), required = True )
    phycounter = fields.Char( 'Other Verification (Wt. or pc)', required = True )
    
    qtcdcbaseuom = fields.Float( 'Qtc DC Base UOM', digits=(8,2), compute='_qtcdcbaseuom' )
    grnmode = fields.Selection( [
            ( 'porder', 'Against Purchase Order' ),
            ( 'subcondc', 'Against Subcon DC' ),
            ], 'Grnmode', readonly = True )
    grnmodedc = fields.Selection( [
            ( 'o', 'Receivable Output Item' ),
            ( 'i', 'Input Item Return' ),
            ( 'b', 'Receivable Byproduct Item' ),
            ], 'DC GRN Item', default='o' )

    @api.multi
    @api.depends('qtydc')
    def _qtcdcbaseuom(self):
        for o in self:
            o.qtcdcbaseuom = o.qtydc
            if o.subcondc_:
                if o.grnmodedc == 'o':
                    o.qtcdcbaseuom = o.qtydc * o.subcondc_.uomconv

    @api.multi
    def grn(self):
        if self.qtyactual <= 0:
            raise exceptions.UserError('Check Actual Qty. Zero Not Allowed')
        balqty = 0
        if self.porder_:
            balqty = self.porder_.balanceqty
        else:
            if not self.subcondc_.processsubcon_:
                if self.grnmodedc != 'i':
                    raise exceptions.UserError('Looks like a returnable item. Select grnmode: Input return as it is')
            if self.grnmodedc == 'o':
                balqty = self.balanceqtydco
            elif self.grnmodedc == 'i':
                balqty = self.balanceqtydci
            elif self.grnmodedc == 'b':
                balqty = self.balanceqtydcb
        if self.qtyactual > balqty:
            raise exceptions.UserError('Check Actual Qty > Balance Qty')
            
        billconv = 1
        if self.subcondc_:
            if self.grnmodedc == 'o':
                if self.subcondc_.uomconv > 0:
                    billconv = self.subcondc_.uomconv
        grnid = self.env['simrp.grn'].create({
            'grnmaster_':self.grnmaster_.id,
            'porder_':self.porder_.id if self.porder_ else False,
            'subcondc_':self.subcondc_.id if self.subcondc_ else False,
            'party_':self.grnmaster_.party_.id,
            'qtydc':self.qtcdcbaseuom,
            'qtyactual':self.qtyactual,
            'phycounter':self.phycounter,
            'grnmodedc':self.grnmodedc,
            'billconv': billconv
            })
        #self.env['simrp.grn'].browse( grnid ).initGRN()
        grnid.initGRN()
        #self.podate = datetime.date.today()
        return grnid

class Tgrnqty(models.TransientModel):
    _name = 'simrp.tgrnqty'
    
    grn_ = fields.Many2one( 'simrp.grn', 'GRN', readonly = True )
    dcno = fields.Char( 'Party DC No.', size = 20, related='grn_.dcno' )
    party_ = fields.Many2one( 'simrp.party', 'Supplier', related='grn_.party_' )
    item_ = fields.Many2one( 'simrp.item', 'Item', related='grn_.item_' )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess', related='grn_.itemprocess_' )
    uom_ = fields.Many2one( 'simrp.uom', 'Base UOM', related='grn_.uom_' ) 

    qtydc = fields.Float( 'DC Quantity', digits=(8,2), related='grn_.qtydc' )
    phycounter = fields.Char( 'Other Verification (Wt. or pc)', related='grn_.phycounter' )
    qtyremarks = fields.Text( 'Qtyremarks', related='grn_.qtyremarks' )

    qtyactual = fields.Float( 'Physical Qty', digits=(8,2), required = True )
    addremarks = fields.Char( 'Qty Remarks', required = True )
    finalize = fields.Boolean( 'Finalise Qty', required = True, default=False )
    
    @api.multi
    def update(self):
        self.grn_.update( self.qtyactual, self.addremarks, self.finalize )
        return { 'type': 'ir.actions.act_view_reload' }
    
class Tgrnservice(models.TransientModel):
    _name = 'simrp.tgrnservice'
    
    grn_ = fields.Many2one( 'simrp.grn', 'GRN', readonly = True )
    dcno = fields.Char( 'Party DC No.', size = 20, related='grn_.dcno' )
    party_ = fields.Many2one( 'simrp.party', 'Supplier', related='grn_.party_' )
    item_ = fields.Many2one( 'simrp.item', 'Item', related='grn_.item_' )
    qtyactual = fields.Float( 'DC Quantity', digits=(8,2), related='grn_.qtyactual' )
    phycounter = fields.Char( 'Other Verification (Wt. or pc)', related='grn_.phycounter' )

    addremarks = fields.Char( 'Service Approval Remarks', required = True )

    @api.multi
    def approve(self):
        self.grn_.approveservice( self.addremarks )
        return { 'type': 'ir.actions.act_view_reload' }
    @api.multi
    def notapprove(self):
        self.grn_.notapproveservice( self.addremarks )
        return { 'type': 'ir.actions.act_view_reload' }
    @api.multi
    def update(self):
        self.grn_.updateservice( self.addremarks )
        return { 'type': 'ir.actions.act_view_reload' }

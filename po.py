# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, exceptions
import logging
_logger = logging.getLogger(__name__)

class Porder(models.Model):
    _name = 'simrp.porder'
    
    name = fields.Char( 'PO Number', size = 50, readonly = True )
    podate = fields.Date( 'PO Date', readonly = True )

    party_ = fields.Many2one( 'simrp.party', 'Supplier', required = True )
    item_ = fields.Many2one( 'simrp.item', 'Item', required = True )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess' )
    
    type = fields.Selection( related='item_.type')    
    
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme', required = True ) 
    rate = fields.Float( 'Basic Rate', digits=(8,2), required = True )
    loadrate = fields.Float( 'Load/Pack Charge', digits=(8,2), default=0 )
    testrate = fields.Float( 'Testing Charge', digits=(8,2), default=0 )
    transportrate = fields.Float( 'Transport Charge', digits=(8,2), default=0 )

    des = fields.Text( 'Special Instructions' )
    advance = fields.Char( 'Advance Paid', default='' )
    deliveryparty_ = fields.Many2one( 'simrp.party', 'Delivery To' )
    
    transport = fields.Selection( [
            ( 'lfob', 'Free Local delivery to transporter' ),
            ( 'cif', 'Free delivery to our works' ),
            ( 'pay', 'Chargeable' ),
            ( 'pick', 'Pickup arranged by us' ),            
            ], 'Transport', default='lfob' )

    uom_ = fields.Many2one( 'simrp.uom', 'Base UOM', related='item_.uom_' ) 
    poqty = fields.Float( 'PO Qty', required = True )

    ordervalue = fields.Integer( 'Basic Order Value', compute='_xordervalue' )
    netvalue = fields.Integer( 'Net Order Value', compute='_xnetvalue' )
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'o', 'Open' ),
            ( 'c', 'Closed' ),
            ], 'State', readonly = True, default='d' )
            
    
    grnqty = fields.Float( 'GRN Qty', readonly = True, compute='_xgrnqty' )
    balanceqty = fields.Float( 'Balance Qty', readonly = True, compute='_xbalanceqty' )
    grn_s = fields.One2many( 'simrp.grn', 'porder_', 'GRNs' )

    wo_ = fields.Many2one( 'simrp.wo', 'WO Link' )
    woitem_ = fields.Many2one( related='wo_.item_' )
    wotqty = fields.Integer( related='wo_.tqty' )
    log = fields.Text( 'Log', readonly = True, default='' )

    
    _order = 'id desc'
    
    @api.multi
    @api.depends('poqty','grnqty')
    def _xbalanceqty(self):
        for o in self:
            o.balanceqty = o.poqty - o.grnqty
            if o.balanceqty < 0:
                o.balanceqty = 0
                
    @api.multi
    @api.depends('grn_s','grn_s.okinqty')
    def _xgrnqty(self):
        for o in self:
            dq = 0
            for d in o.grn_s:
                dq = dq + d.okinqty
            o.grnqty = dq


    @api.multi
    @api.depends( 'poqty', 'rate', 'transportrate', 'testrate', 'loadrate' )
    def _xordervalue(self):
        for o in self:
            o.ordervalue = ( o.poqty * o.rate ) + o.transportrate + o.testrate + o.loadrate

    @api.multi
    @api.depends( 'poqty', 'rate', 'transportrate', 'testrate', 'loadrate', 'taxscheme_', 'taxscheme_.taxline_s', 'taxscheme_.taxline_s.sequence', 'taxscheme_.taxline_s.rate', 'taxscheme_.taxline_s.on' )
    def _xnetvalue(self):
        for o in self:
            #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> compute call" )
            tv = o.taxscheme_.compute( o.ordervalue )
            o.netvalue = o.ordervalue + tv[ 'tax' ]
    
    @api.multi
    def close(self):
        self.state = 'c'
        return True
    @api.multi
    def redraft(self):
        self.state = 'd'
        return True
        
    @api.multi
    def approve(self):
        if self.item_.state != 'a':
            raise exceptions.UserError('Item not yet approved')    
        if self.item_.hsnsac == '':
            raise exceptions.UserError('Item HSN/SAC Information missing')   
        if self.item_.type in ['rmb','bo']:
            if not self.wo_:
                raise exceptions.UserError('WO Linkage is necessary for this item type.')   
        self.state = 'o'
        self.name = self.env['ir.sequence'].next_by_code('simrp.porder')
        self.podate = datetime.date.today()
        self.env[ 'simrp.auditlog' ].log( self, 'PO Approve:', self.read( self.logfields )[0], True, False )
        
        return True

    logfields = [ 'name', 'party_', 'item_', 'poqty', 'rate', 'taxscheme_', 
                    'loadrate', 'testrate', 'transportrate', 'deliveryparty_', 'transport' ]

        
    @api.multi
    def reopen(self):
        self.state = 'o'
        return True

    @api.multi
    def printpo(self):
        return self.env.ref('simrp.action_report_printpo').report_action(self)

    @api.multi
    def sendemail(self):
        return True

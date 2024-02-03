# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Csubcondc(models.Model):
    _name = 'simrp.csubcondc'

    recdate = fields.Datetime( 'Time', readonly = True, default=lambda self: fields.Datetime.now() )
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    itemrate_ = fields.Many2one( 'simrp.itemrate', 'Customer Process', required = True )

    partydc = fields.Char( 'Party dc', size = 20 )
    partydcdate = fields.Date( 'Party dc date', default=lambda self: fields.Date.today() )
    qtydc = fields.Float( 'DC Qty', digits=(8,2) )
    inqty = fields.Float( 'Qty In', digits=(8,2), required = True )
    crosscheck = fields.Char( 'Crosscheck Weight', size = 200, required = True )
    
    name = fields.Char( 'Inward Code', size = 20, readonly = True, default='<draft>' )
    
    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Saleorder', readonly = True )
    cmdc_s = fields.One2many( 'simrp.cmdc', 'csubcondc_', 'Customer Material DCs', readonly = True )

    item_ = fields.Many2one( 'simrp.item', 'Input Item', related='itemrate_.inputitem_', readonly = True )
    itemtype = fields.Selection( related='item_.type', string='Item Type' )
    itemprocess_ = fields.Many2one('simrp.itemprocess', related='itemrate_.itemprocess_' )
    outputitem_ = fields.Many2one('simrp.item', related='itemrate_.item_' )
    byproductitem_ = fields.Many2one('simrp.item', related='itemrate_.byproductitem_' )
    inputuom_ = fields.Many2one( 'simrp.uom', 'UOM', related='itemrate_.inputuom_' )
    outputuom_ = fields.Many2one( 'simrp.uom', related='itemrate_.outputuom_' )
    byproductuom_ = fields.Many2one( 'simrp.uom', related='itemrate_.byproductuom_' )
    opconv = fields.Float( related='itemrate_.opconv' )
    byconv = fields.Float( related='itemrate_.byconv' )
    scrappolicy = fields.Selection( related='itemrate_.scrappolicy' )
    transport = fields.Selection( related='itemrate_.transport' )

    outputexpected = fields.Float( 'Output expected', digits=(8,2), readonly = True )
    byproductexpected = fields.Float( 'By-product expected', digits=(8,2), readonly = True )

    balanceqtyo = fields.Float( 'Balance Qty of Output Item', digits=(8,2), compute='_balanceqtyo' )
    balanceqtyi = fields.Float( 'Balance Qty of Input Item', digits=(8,2), compute='_balanceqtyi' )
    balanceqtyb = fields.Float( 'Balance Qty of By-product Item', digits=(8,2), compute='_balanceqtyb' )

    dispatch_s = fields.One2many( 'simrp.dispatch', 'saleorder_', related='saleorder_.dispatch_s' )
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'o', 'Open' ),
            ( 'c', 'Closed' ),
            ], 'State', default='d' )

    _order = 'id desc'
    
    def close( self ):
        self.state = 'c'
        self.env[ 'simrp.auditlog' ].log( self, 'Customer SDC CLOSE:', self.read( [ 'name', 'party_', 'item_', 'inqty'  ] )[0], False, False )
        return True

    @api.multi
    @api.depends('inqty','cmdc_s','cmdc_s.qtyi','dispatch_s','dispatch_s.okoutqty')
    def _balanceqtyi(self):
        for o in self:
            dq = o.inqty
            for d in o.cmdc_s:
                dq = dq - d.qtyi
            for d in o.dispatch_s:
                if o.opconv > 0:
                    dq = dq - ( d.okoutqty / o.opconv )
            if dq < 0:
                dq = 0
            o.balanceqtyi = dq

    @api.multi
    @api.depends('outputexpected','dispatch_s','dispatch_s.okoutqty')
    def _balanceqtyo(self):
        for o in self:
            o.balanceqtyo = o.balanceqtyi * o.itemrate_.opconv

    @api.multi
    @api.depends('inqty','cmdc_s','cmdc_s.qtyb', 'byproductexpected')
    def _balanceqtyb(self):
        for o in self:
            dq = 0
            for d in o.dispatch_s:
                dq = dq + d.okoutqty
            dq = dq * o.itemrate_.byconv
            for d in o.cmdc_s:
                dq = dq - d.qtyb
            if dq < 0:
                dq = 0
            o.balanceqtyb = dq
            
    def confirm( self ):
        if self.qtydc != self.inqty:
            raise exceptions.UserError('DC Qty and Actual qty mismatch')
        if self.qtydc <= 0:
            raise exceptions.UserError('DC Qty > 0')
        if not self.itemprocess_:
            raise exceptions.UserError('Item process should be defined in item rate agreement')
        if not self.item_:
            raise exceptions.UserError('Item process and item rate agreement should have input item')
        wos = self.env[ 'simrp.wo' ].search( [ ('item_','=',self.outputitem_.id), ('state','=','o') ], order='id desc' )
        if not wos:
            raise exceptions.UserError('No open WO found for this item')
        
        wo = wos[ 0 ]
        
        self.outputexpected = self.inqty * self.itemrate_.opconv
        self.byproductexpected = self.inqty * self.itemrate_.byconv
        
        self.saleorder_ = self.env[ 'simrp.saleorder' ].create( {
                'party_': self.party_.id,
                'pono': self.itemrate_.customerpo,
                'podate': self.itemrate_.customerpodate,
                'itemrate_': self.itemrate_.id,
                'poqty': self.outputexpected,
                'commitdate': fields.Date.today(),
                'state': 'o',
                } )
        
        wo.tqty = wo.tqty + self.outputexpected
        wo.refresh()

        woissue = self.env['simrp.woissue'].create( { 
                                'wo_': wo.id, 
                                'wobom_': wo.wobom_s[0].id, 
                                'lotno': self.partydc,
                                'iqty': self.inqty
                                } )
        
        self.state = 'o'
        self.name = self.env['ir.sequence'].next_by_code('simrp.csubcondc')
        self.env[ 'simrp.auditlog' ].log( self, 'Customer SDC:', self.read( [ 'name', 'party_', 'item_', 'inqty', 'crosscheck'  ] )[0], False, False )
        return True


class Cmdc(models.Model):
    _name = 'simrp.cmdc'

    name = fields.Char( 'DC No.', size = 20, readonly = True )
    dcdate = fields.Date( 'DC Date', default=lambda self: fields.Date.today(), readonly = True )
    csubcondc_ = fields.Many2one( 'simrp.csubcondc', 'Subcon DC', readonly = True )

    party_ = fields.Many2one( 'simrp.party', 'Supplier', related='csubcondc_.party_' )
    itemdci_ = fields.Many2one( 'simrp.item', 'Return Input Item', related='csubcondc_.itemrate_.inputitem_' )
    itemdcb_ = fields.Many2one( 'simrp.item', 'Return By-product Item', related='csubcondc_.itemrate_.byproductitem_' )    
    inputuom_ = fields.Many2one( 'simrp.uom', 'UOM', related='itemdci_.uom_' )
    byproductuom_ = fields.Many2one( 'simrp.uom', related='itemdcb_.uom_' )

    balanceqtydci = fields.Float( 'Balance Input Qty', digits=(8,2), related='csubcondc_.balanceqtyi' )
    balanceqtydcb = fields.Float( 'Balance By-product Qty', digits=(8,2), related='csubcondc_.balanceqtyb' )
    
    qtyi = fields.Float( 'Qty Input Return', digits=(8,2), default=0 )
    qtyb = fields.Float( 'Qty By-product Return', digits=(8,2), default=0 )
    phycounter = fields.Char( 'Other Verification (Wt. or pc)', required = True )

    @api.model
    def create(self, vals):
        csubcondc = self.env[ 'simrp.csubcondc' ].browse( self.env.context[ 'default_csubcondc_' ] )
        if vals[ 'qtyi' ] + vals[ 'qtyb' ] == 0:
            raise exceptions.UserError('Enter qty details')
        if vals[ 'qtyi' ] > csubcondc.balanceqtyi:
            raise exceptions.UserError('Given qty exceeds balance qty')
        if vals[ 'qtyb' ] > csubcondc.balanceqtyb:
            raise exceptions.UserError('Given qty exceeds balance qty')
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.cmdc')
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Customer SDC Return:', o.read( [ 'name', 'party_' ] )[0], False, False )        
        return o

    @api.multi
    def print(self):
        return self.env.ref('simrp.action_report_printcmdc').report_action(self)

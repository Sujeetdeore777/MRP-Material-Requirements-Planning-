# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Subcondc(models.Model):
    _name = 'simrp.subcondc'
    # _inherits = {'simrp.stock': 'stock_'} 
    
    #stock_ =  fields.Many2one( 'simrp.stock', 'Stock old field', readonly=True)

    recdate = fields.Datetime( 'Time', readonly = True, default=lambda self: fields.Datetime.now() )

    party_ = fields.Many2one( 'simrp.party', 'Party' )
    item_ = fields.Many2one('simrp.item', 'Item' )
    
    itemtype = fields.Selection( related='item_.type', string='Item Type' )
    itemuom_ = fields.Many2one( related='item_.uom_' ) 
    
    okinqty = fields.Float( 'Ok In', digits=(8,2), default=0 )
    rejinqty = fields.Float( 'Rej In', digits=(8,2), default=0 )
    okoutqty = fields.Float( 'Ok Out', digits=(8,2), default=0 )
    rejoutqty = fields.Float( 'Rej Out', digits=(8,2), default=0 )


    #item_ inputitem_ = fields.Many2one('simrp.item', 'Input item', required = True )
    #party_
    #recdate
    #ref
    #okoutqty of inputitem in baseuom

    processsubcon_ = fields.Many2one( 'simrp.processsubcon', 'Subcon Process', readonly = True )
    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    wostate = fields.Selection( related='wo_.state' )

    name = fields.Char( 'DC no', size = 20, required = True, default='<draft>' )

    dcalternateqty = fields.Float( 'Alternate Qty (For DC)', digits=(8,2), readonly = True )
    outputexpected = fields.Float( 'Output expected', digits=(8,2), readonly = True )
    byproductexpected = fields.Float( 'By-product expected', digits=(8,2), readonly = True )
    crosscheck = fields.Char( 'Crosscheck Weight', size = 100, default="" )
    
    code = fields.Char('Subcon Agreement Code', related='processsubcon_.code')
    itemprocess_ = fields.Many2one('simrp.itemprocess', related='processsubcon_.itemprocess_' )
    outputitem_ = fields.Many2one('simrp.item', related='processsubcon_.item_' )
    byproductitem_ = fields.Many2one('simrp.item', related='processsubcon_.byproductitem_' )
    inputuom_ = fields.Many2one( 'simrp.uom', 'UOM', related='processsubcon_.inputuom_' )
    outputuom_ = fields.Many2one( 'simrp.uom', related='processsubcon_.outputuom_' )
    byproductuom_ = fields.Many2one( 'simrp.uom', related='processsubcon_.byproductuom_' )
    opconv = fields.Float( related='processsubcon_.opconv' )
    byconv = fields.Float( related='processsubcon_.byconv' )
    rateuom_ = fields.Many2one( 'simrp.uom', 'Alternate UOM', related='processsubcon_.rateuom_' )
    uomconv = fields.Float( related='processsubcon_.uomconv' )
    scrappolicy = fields.Selection( related='processsubcon_.scrappolicy' )
    transport = fields.Selection( related='processsubcon_.transport' )

    balanceqtyo = fields.Float( 'Balance Output', digits=(8,2), compute='_balanceqtyo' )
    balanceqtyi = fields.Float( 'Balance Input', digits=(8,2), compute='_balanceqtyi' )
    balanceqtyb = fields.Float( 'Balance By-product', digits=(8,2), compute='_balanceqtyb' )
    balanceqtyoruom = fields.Float( 'Balance Output (RUOM)', digits=(8,2), compute='_balanceqtyoINrateuom' )

    #rate = fields.Float( related='processsubcon_.rate' )
    grn_s = fields.One2many( 'simrp.grn', 'subcondc_', 'GRNs' )
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'o', 'Open' ),
            ( 'c', 'Closed' ),
            ], 'State', default='d' )

    _order = 'id desc'




    
    # @api.multi
    @api.depends('outputexpected','grn_s','grn_s.okinqty')
    def _balanceqtyo(self):
        for o in self:
            o.balanceqtyo = o.balanceqtyi * o.opconv

    @api.multi
    @api.depends('outputexpected','grn_s','grn_s.okinqty')
    def _balanceqtyoINrateuom(self):
        for o in self:
            o.balanceqtyoruom = 0
            if o.uomconv > 0:
                o.balanceqtyoruom = o.balanceqtyo / o.uomconv
            
    @api.multi
    @api.depends('okoutqty','grn_s','grn_s.okinqty')
    def _balanceqtyi(self):
        for o in self:
            dq = o.okoutqty         #material sent for processing, if processsubcon_ is false, grn should be of this type
            for d in o.grn_s:
                if d.grnmodedc == 'i':
                    dq = dq - d.okinqty
                if d.grnmodedc == 'o':
                    dq = dq - ( d.okinqty / o.opconv )
            if dq < 0:
                dq = 0
            o.balanceqtyi = dq

    @api.multi
    @api.depends('byproductexpected','grn_s','grn_s.okinqty')
    def _balanceqtyb(self):
        for o in self:
            dq = 0
            for d in o.grn_s:
                if d.grnmodedc == 'o':
                    dq = dq + d.okinqty
            dq = dq * o.byconv
            for d in o.grn_s:
                if d.grnmodedc == 'b':
                    dq = dq - d.okinqty
            if dq < 0:
                dq = 0
            o.balanceqtyb = dq

    @api.model
    def create( self, vals ):
        o = super(Subcondc, self).create(vals)
        #o.rate = o.processsubcon_.rate
        # o.stock_.initStock( o.processsubcon_.inputitem_, 'simrp.subcondc', o.id, o.processsubcon_.party_ )
        if o.processsubcon_:
            o.party_ = o.processsubcon_.party_.id
            o.item_ = o.processsubcon_.inputitem_.id
        return o

    @api.multi
    def cancelDC( self ):
        # self.stock_.sudo().unlink()
        self.sudo().unlink()
        action = self.env.ref('simrp.simrp_subcondc_action').read()[0]   
        return action

    @api.multi
    def initDC( self ):
        """
        1000 pc adaptor                                1000 kg rod
        for plating in kg                               for parting to pc
        uomconv = 17 (17 pc adaptors per kg)           0.2 (0.2kg rod per pc)
        altq = 1000/17                                  NO uomconv here are party is going to bill in output item's baseUOM
        """
        if self.okoutqty <= 0:
            raise exceptions.UserError('Qty should be greater than 0')
        if self.crosscheck == "":
            raise exceptions.UserError('Enter cross check qty/remarks (For qty dispute resolution)')
        self.outputexpected = self.okoutqty * self.opconv
        self.dcalternateqty = 0
        if self.uomconv > 0:
            self.dcalternateqty = self.outputexpected / self.uomconv
        self.byproductexpected = self.outputexpected * self.byconv        
        self.confirmDC()
        return True
        
    @api.multi
    def confirmDC( self ):
        self.state = 'o'
        self.name = self.env['ir.sequence'].next_by_code('simrp.subcondc')
        self.env[ 'simrp.auditlog' ].log( self, 'SDC:', self.read( self.logfields )[0], False, False )        
        return True        

    logfields = [ 'name', 'processsubcon_', 'wo_', 'party_', 'okoutqty', 'dcalternateqty', 'outputexpected', 'crosscheck', 'code', 'item_', 'itemprocess_' ]

    @api.multi
    def printDC(self):
        return self.env.ref('simrp.action_report_printsdc').report_action(self)


    @api.multi
    def close(self):
        self.state = 'c'
        return True

    def qtyclose(self):
        if ( ( self.balanceqtyb > 0.9 ) or ( self.balanceqtyi > 0.5 ) or ( self.balanceqtyo >= 1 ) ):
            raise exceptions.UserError('All balance Qty should be 0')
        else:
            self.state = 'c'
        return True


class Treturnabledc(models.TransientModel):
    _name = 'simrp.treturnabledc'
    
    item_ = fields.Many2one('simrp.item', 'Item to send', required = True )
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    qty = fields.Float( 'Qty', digits=(8,2), required = True )
    crosscheck = fields.Text( 'Crosscheck / Accessory List', required = True )

    @api.multi
    def createDC( self ):
        dc = self.env[ 'simrp.subcondc' ].create( {
            'item_': self.item_.id,
            'party_': self.party_.id,
            'okoutqty': self.qty,
            'processsubcon_': False,
            'dcalternateqty': 0,
            'outputexpected': 0,
            'byproductexpected': 0,
            'crosscheck': self.crosscheck,
            'state': 'o'
        } )
        dc.confirmDC()
        dc.name = dc.name + '-T'
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.subcondc',
            'target': 'current',
            'res_id': dc.id,
            'context': {'force_detailed_view': 'true'},
            }

    
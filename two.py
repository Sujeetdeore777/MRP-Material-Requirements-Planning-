# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Two(models.TransientModel):
    _name = 'simrp.two'
    
    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    woitem_ = fields.Many2one( related='wo_.item_' )

    wobom_ = fields.Many2one( 'simrp.wobom', 'Wobom' )
    lotno = fields.Char( 'Manual Lot no', size = 200 )
    iqty = fields.Float( 'Iqty', digits=(8,2) )

    fgokqty = fields.Float( 'OK Mfg Qty', digits=(8,2) )
    fgrejqty = fields.Float( 'Rej Mfg Qty', digits=(8,2) )

    type = fields.Selection( [
            ( 'woissue', 'Issue Material to WO' ),
            ( 'fg', 'FG Stock Booking' ),
#            ( '', '' ),
            ], 'Type', readonly = True )

    @api.multi
    def bomissue( self ):
        if not self.wobom_:
            raise exceptions.UserError('Select Item to issue')
        if self.iqty <= 0:
            raise exceptions.UserError('Issue Qty Should be > 0')
        woissue = self.env['simrp.woissue'].create( { 
                                'wo_': self.wo_.id, 
                                'wobom_': self.wobom_.id, 
                                'lotno': self.lotno,
                                'iqty': self.iqty
                                } )
        self.env[ 'simrp.auditlog' ].log( self.wo_, 'WO RM Issue: ' + self.wobom_.bomitem_.name + ' [' + str( self.iqty ) + ']', self.wo_.read( [ 'name', 'item_', 'tqty', 'saleorder_' ] )[0], False, False )
        return { 'type': 'ir.actions.act_view_reload' }

    @api.multi
    def mfg( self ):
        if self.fgokqty + self.fgrejqty <= 0:
            raise exceptions.UserError('Mfg Qty Should be > 0')
        womfg = self.env['simrp.womfg'].create( { 
                                'wo_': self.wo_.id, 
                                'okqty': self.fgokqty,
                                'rejqty': self.fgrejqty
                                } )
        if self.wo_.type == 'n':
            womfg.initStock()
        self.env[ 'simrp.auditlog' ].log( self.wo_, 'WO FG Book: ' + ' [' + str( self.fgokqty ) + ' / ' + str( self.fgrejqty ) + ']', self.wo_.read( [ 'name', 'item_', 'tqty', 'saleorder_' ] )[0], False, False )
        return { 'type': 'ir.actions.act_view_reload' }
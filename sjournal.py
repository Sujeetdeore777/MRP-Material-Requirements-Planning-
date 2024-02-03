# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Sjournal(models.Model):
    _name = 'simrp.sjournal'

    name = fields.Char( 'Stock journal', size = 20, readonly = True )
    
    itemfrom_ = fields.Many2one( 'simrp.item', 'Item From', domain=[('state', '=', 'a')], required = True )
    okoutqty = fields.Float( 'Ok Out', digits=(8,2), default=0 )
    rejoutqty = fields.Float( 'Rej Out', digits=(8,2), default=0 )

    itemto_ = fields.Many2one( 'simrp.item', 'Item To', domain=[('state', '=', 'a')], required = True )
    okinqty = fields.Float( 'Ok In', digits=(8,2), default=0 )
    rejinqty = fields.Float( 'Rej In', digits=(8,2), default=0 )
    
    des = fields.Char( 'Description', size = 500 )
    recdate = fields.Date( 'Rec date', readonly = True )
    
    @api.model
    def create(self, vals):
        # if ( vals[ 'okoutqty' ] + vals[ 'rejoutqty' ] ) != ( vals[ 'okinqty' ] + vals[ 'rejinqty' ] ):
            # raise exceptions.ValidationError('Out and In qty are not equal.')
        vals[ 'recdate' ] = fields.Date.today()
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.sjournal')
        o = super(Sjournal, self).create(vals)
        ref = '%s,%s' % ( 'simrp.sjournal', o.id )
        self.env[ 'simrp.stock' ].create( {
            'ref': ref,
            'item_': o.itemfrom_.id,
            'okoutqty': o.okoutqty,
            'rejoutqty': o.rejoutqty,
        } )
        self.env[ 'simrp.stock' ].create( {
            'ref': ref,
            'item_': o.itemto_.id,
            'okinqty': o.okinqty,
            'rejinqty': o.rejinqty
        } )
        self.env[ 'simrp.auditlog' ].log( o, 'Stock JOURNAL:', o.read()[0], False, False )                
        return o
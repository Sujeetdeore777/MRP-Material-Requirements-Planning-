# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Partymaterial(models.Model):
    _name = 'simrp.partymaterial'

    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    partydc = fields.Char( 'Party DC', size = 20 )
    partydcdate = fields.Date( 'Party DC date', default=lambda self: fields.Date.today() )
    
    itemdes = fields.Text( 'Item Description (1 item per record)', required = True )
    
    name = fields.Char( 'Tx No', size = 20, readonly = True )
    rdate = fields.Date( 'Rdate', readonly = True )
    
    ackt = fields.Char( 'Acknowledgement Proof details', size = 200 )
    
    state = fields.Selection( [
            ( 'mus', 'material with us' ),
            ( 'mr', 'material returned' ),
            ( 'ack', 'DC Acknowledged' ),
            ], 'State', readonly = True, default='mus' )

    @api.model
    def create(self, vals):
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Party Material:', o.read()[0], False, False )
        return o
            
    def send( self ):
        self.state = 'mr'
        self.rdate = fields.Date.today()
        self.name = self.env['ir.sequence'].next_by_code('simrp.partymaterial')
        self.env[ 'simrp.auditlog' ].log( self, 'Party Material Wait for ACK:', self.read()[0], False, False )
        return True
        
    def ack( self ):
        if (not self.ackt) or self.ackt == "":
            raise exceptions.UserError('Enter Acknowledgement Proof details')
        self.state = 'ack'
        return True

    def printDC(self):
        return self.env.ref('simrp.action_report_printtmdc').report_action(self)

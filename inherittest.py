# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, exceptions
from dateutil.relativedelta import relativedelta
from . import shiftinfo
from num2words import num2words
from urllib.parse import quote
import base64
import json
import re
import pytz

import logging
_logger = logging.getLogger(__name__)

class Loghistory( models.Model ):
    _name = 'simrp.loghistory'
    
    log = fields.Text( 'Log', default='' )
    seen = fields.Selection( [
            ( 'u', 'Unseen' ),
            ( 's', 'Seen' ),
            ( 'm', 'Marked' ),
            ], 'Seen', default='u' )

class Loghistory1( models.AbstractModel ):
    _name = 'simrp.loghistory1'
    
    log1 = fields.Text( 'Log', default='' )
    seen1 = fields.Selection( [
            ( 'u', 'Unseen' ),
            ( 's', 'Seen' ),
            ( 'm', 'Marked' ),
            ], 'Seen', default='u' )

    @api.model
    def create( self, vals ):
        _logger.info( '############# ' )
        _logger.info( vals )
        return super(Loghistory1, self).create(vals)

    def write( self, vals ):
        _logger.info( '############# ' )
        _logger.info( vals )
        return super(Loghistory1, self).write(vals)
        
    @api.multi
    def mark( self ):
        for o in self:
            o.seen1 = 'm'
    
class Dummy(models.Model):
    _name = 'simrp.dummy'
    _inherits = {'simrp.loghistory': 'loghistory_'} 
    _inherit = 'simrp.loghistory1'
    loghistory_ =  fields.Many2one( 'simrp.loghistory', 'LogHistory', required=True, ondelete="cascade")

    name = fields.Char( 'DC No', size = 50, default='<draft>' )
    rate = fields.Float( 'Rate', digits=(8,2) )

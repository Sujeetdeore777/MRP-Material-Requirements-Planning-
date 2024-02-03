# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, exceptions
from dateutil.relativedelta import relativedelta
from . import shiftinfo
import json
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import date_utils

import logging
_logger = logging.getLogger(__name__)

class Auditlog(models.Model):
    _name = 'simrp.auditlog'

    auditlog = fields.Text( 'Audit Log', readonly = True )
    active = fields.Boolean( 'Active', default=True, readonly = True )

    ref = fields.Reference( [], string='Document', readonly = True )  

    state = fields.Selection( [
            ( 'i', 'Info' ),
            ( 'm', 'Mark' ),
            ( 's', 'Seen' ),
            ], 'State',default='i', readonly = True )

    _order = 'id desc'

        # # Code before write: can use `self`, with the old values 
        # super(Employee, self).write(vals)
        # # Code after write: can use `self`, with the updated values 


    @api.model
    def log( self, o, log, vals={}, logfieldupdate=True, logdiff=True, trimlimit=30 ):
        vi = log + ' { '
        for v in vals:
            if v not in [ 'create_uid', 'create_date', 'write_uid', 'write_date', 'display_name', '__last_update' ]:
                if logdiff:
                    vi = vi + o._fields[ v ].string + ': ' + json.dumps( o[ v ], default=date_utils.json_default)[:trimlimit] + ' => ' + json.dumps( vals[ v ], default=date_utils.json_default)[:trimlimit] + ', '
                else:
                    vi = vi + v + ': ' + json.dumps( vals[ v ], default=date_utils.json_default)[:trimlimit] + ', '
        vi = vi + '}'

        self.create( { 'auditlog': vi, 'ref': '%s,%s' % ( o._name, o.id ) } )
        if logfieldupdate:
            if not o.log:
                o.log = ''
            # _logger.info( self.env.user.id )
            # _logger.info( self.env.user.tz )
            
            o.log = o.log + "[" + self.env.user.name + " - " + pytz.utc.localize( fields.Datetime.now() ).astimezone( pytz.timezone( self.env.user.tz or str(pytz.utc) ) ).strftime( DEFAULT_SERVER_DATETIME_FORMAT ) + "] " + vi + '\n'


    def info( self ):
        for o in self:
            o.state = 'i'
            
    def mark( self ):
        for o in self:
            o.state = 'm'
            
    def seen( self ):
        for o in self:
            o.state = 's'
            o.active = False
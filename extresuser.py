# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class Extresuser(models.Model):
    #_name = 'res.users'
    _inherit = 'res.users'
    
    group = fields.Selection( [
            ( 's', 'S' ),
            ( 'v', 'V' ),
            ], 'Group', default='s', readonly = True )
            
    #need to do a cmdline upgrade
    

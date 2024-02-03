# -*- coding: utf-8 -*-

import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Tpay(models.Model):
    _name = 'simrp.tpay'
    
    name = fields.Char( 'Tpay Reference', size = 20, required = True )
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        _logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>> context: " + self.env.context )
        result = super(AccountMoveLine, self).fields_view_get(view_id, view_type, toolbar, submenu)
        return result
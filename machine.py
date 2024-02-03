# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class Machine(models.Model):
    _name = 'simrp.machine'
    
    name = fields.Char( 'Machine Name', size = 50 )
    viilinkcode = fields.Char( 'Vii link code', size = 50 )
# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Toolissue(models.Model):
    _name = 'simrp.toolissue'
    
    name = fields.Char( 'Toolissue', size = 50 )
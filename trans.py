import datetime
from odoo import api, fields, models, exceptions
from odoo.exceptions import ValidationError

import base64
import datetime


class trans(models.TransientModel):
    _name = 'simrp.trans'
    _description = 'trans'

    invoice_ = fields.Many2one( 'simrp.invoice', 'Invoice', required = True )

    

 
            
   
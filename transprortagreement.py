import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Transportagreement(models.Model):
    _name = 'simrp.transportagreement'

    date = fields.Date( 'Agreement Date', default=lambda self: fields.Date.today(), required = True )
    party_ = fields.Many2one( 'simrp.party', 'Transporter Name', required = True)
    tadetail_s = fields.One2many( 'simrp.tadetail', 'transportagreement_', 'Transport Agreement' )
    log = fields.Text( 'Log', readonly = True )

    @api.model
    def create(self, vals):
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Create Tran. Agreement: ', {}, True, False )
        return o

    def write(self, vals):
        if 'log' not in vals:
            self.env[ 'simrp.auditlog' ].log( self, 'Change Tran. Agreement:', vals, True, True, 1000 )
        return super().write(vals)

class Tadetail(models.Model):
    _name = 'simrp.tadetail'

    transportagreement_ = fields.Many2one( 'simrp.transportagreement', 'Party Name', required = True)
    name = fields.Char( 'Trip Type', size = 50, required = True )
    rate = fields.Integer( 'Amount', default=0, required = True )


import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import shiftinfo

class Leave(models.Model):
    _name = 'simrp.leave_req'

    employee_ = fields.Many2one( 'simrp.employee', 'Employee', required = True )
    from_date = fields.Date( 'From Date', required = True )
    fromdate_half = fields.Boolean( 'Half day', default=False )
    to_date = fields.Date( 'To Date', required = True )
    # todate_half = fields.Boolean( 'Half day for end day', default=False )
    reason = fields.Char( 'Reason', size = 100, required = False )
    status = fields.Selection( [
            ( 'Approved', 'Approved' ),
            ( 'Unapproved', 'Unapproved' ),
            ], 'Status', default='Unapproved', required = True, readonly = True )

    _order = 'id desc'

    def apprv(self):
        self.update({'status':'Approved'})
        return True

    def unapprove(self):
        self.update({'status':'Unapproved'})
        return True

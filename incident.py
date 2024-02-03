import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class IncidentRecords(models.Model):
    _name = 'simrp.incident'

    name = fields.Char( 'Incident No', size = 10, readonly = True )
    datetime = fields.Datetime( 'Incident Time', default=lambda self: fields.datetime.now(), required = True )
    employee_ = fields.Many2one( 'simrp.employee', 'Employee Name', required = True)
    short_des = fields.Char( 'Short Description', size = 200 )
    des = fields.Text( 'Description' )
    type = fields.Selection( [
            ( 'Green', 'Appreciation' ),
            ( 'Yellow', 'Complaint: Warning / Monitoring' ),
            ( 'Red', 'Fault: Damages / Behavioural / Absentism / Quality' ),
            ], 'Type', default='Green' )
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'c', 'Confirmed' ),
            ], 'State', default='d', readonly = True )
    cost = fields.Integer( 'Cost Impact', default=0, required = False )
    penalty = fields.Integer( 'Penalty', default=0, required = False )
    file1 = fields.Binary(string="File Attachment 1", attachment=True)
    file2 = fields.Binary(string="File Attachment 2", attachment=True)
    file3 = fields.Binary(string="File Attachment 3", attachment=True)
    storename1 = fields.Char( 'Name' )
    storename2 = fields.Char( 'Name' )
    storename3 = fields.Char( 'Name' )

    _order = 'datetime desc'

    @api.model
    def create(self, vals):
        return super(IncidentRecords, self).create(vals)

    @api.multi 
    def confirm( self ): 
        self.name = self.env['ir.sequence'].next_by_code('simrp.incident')
        self.state = 'c'
        return True

    @api.multi 
    def rework( self ): 
        self.state = 'd'
        return True
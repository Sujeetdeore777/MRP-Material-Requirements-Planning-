
import odoo.tools as tools
import datetime
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from dateutil.rrule import rrule, DAILY
from . import shiftinfo


class Reportx(models.TransientModel):
    _name = 'report.simrp.cashreportx'
    _inherit = 'report.report_xlsx.abstract'

    fromdate = fields.Date( 'From Date', default=lambda self: fields.Date.today() )
    todate = fields.Date( 'To Date', default=lambda self: fields.Date.today() )
    type = fields.Selection( [
            ( 'cash', 'Cash Management Report' ),
            ( 'cashexprecord', 'Expense Management Report' ),
            ], 'Report Type', default='cash', required=True )

    @api.multi
    def generate( self ):
        data = {}
        return self.env.ref('simrp.simrp_cashreportx').report_action(self, data)

    def generate_xlsx_report(self, workbook, data, o):
        bold = workbook.add_format({'bold': True, 'bg_color': 'yellow'})

        f = ""
        if o.type == 'cash':
            f = '/simrp/cashstat.rx.py'
        if o.type == 'cashexprecord':
            f = '/simrp/cashrecord.rx.py'
        if f != "":
            cmd = ""
            with open( tools.config['addons_path'] + f, 'r') as file:
                cmd = file.read()
                _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )

            exec( cmd )
            r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
            #r.report_file = o.type + "AAA"
            r.sudo().report_file = o.type + "AAA"
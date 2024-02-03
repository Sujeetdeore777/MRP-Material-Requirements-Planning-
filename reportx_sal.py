# -*- coding: utf-8 -*-

import odoo.tools as tools
import datetime
from odoo import api, fields, models, exceptions 
import logging
_logger = logging.getLogger(__name__)
from dateutil.rrule import rrule, DAILY
from . import shiftinfo


class Reportx(models.TransientModel):
    _name = 'report.simrp.reportx_sal'
    _inherit = 'report.report_xlsx.abstract'

    monthempsalary_ = fields.Many2one( 'simrp.monthempsalary', 'Month salary', required = True )
    bu_ = fields.Many2one( 'simrp.bu', 'BU',required = True )
    fromdate = fields.Date( 'From Date', compute="_fromdate" )
    todate = fields.Date( 'To Date', compute="_fromdate" )
    type = fields.Selection( [
            # ( 'cash', 'Cash salary report (to date)' ),
            ( 'register', 'Register Report' ),
            ], 'Report Type', default='cash', required=True )
    csv = fields.Text( 'CSV', readonly=True )
    
    @api.multi
    def generate( self ):
        data = {}
        return self.env.ref('simrp.simrp_reportx_sal').report_action(self, data)

    @api.multi
    @api.depends('monthempsalary_')
    def _fromdate( self ):
        for o in self:
            if o.monthempsalary_:
                dt = o.monthempsalary_.month_end
                o.todate = dt
                o.fromdate = datetime.date(dt.year, dt.month,1)

    @api.model
    def generate_xlsx_report(self, workbook, data, o):
        bold = workbook.add_format({'bold': True, 'bg_color': 'yellow'})

        f = ""
        if o.type == 'cash':
            f = '/simrp/salarycash.rx.py'
        if o.type == 'register':
            f = '/simrp/register.rx.py'
            
        if f != "":
            cmd = ""
            with open( tools.config['addons_path'] + f, 'r') as file:
                cmd = file.read()
                _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )

            exec( cmd )
            r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
            r.report_file = o.type + '-' + o.bu_.name
            #r.sudo().report_file = o.type + "-" + self.env.cr.dbname + "-" + o.monthempsalary_.month_end
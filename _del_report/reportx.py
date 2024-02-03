# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models
    
class Reportx(models.AbstractModel):
    _name = 'report.simrp.report1'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet( "WS1" )
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 0, "ABCD", bold)

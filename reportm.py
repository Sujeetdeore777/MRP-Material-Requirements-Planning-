# -*- coding: utf-8 -*-

import odoo.tools as tools
import datetime
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from dateutil.rrule import rrule, DAILY
from . import shiftinfo
    
class Reportm(models.TransientModel):
    _name = 'report.simrp.reportm'
    _inherit = 'report.report_xlsx.abstract'

    fromdate = fields.Date( 'From Date', default=lambda self: fields.Date.today() )
    todate = fields.Date( 'To Date', default=lambda self: fields.Date.today() )
    type = fields.Selection( [
            ( 'ss', 'Stock Statement OK' ),
            ( 'ssrej', 'Stock Statement Rej' ),
            ( 'tr', 'Transaction Report' ),
            ], 'Report Type', default='ss', required=True )
    csv = fields.Text( 'Log CSV', readonly=True )
    reportdetails_s = fields.One2many( 'simrp.reportdetails', 'reportm_', 'Result', readonly = True )
    state = fields.Selection( [
            ( 'p', 'Prepare' ),
            ( 'g', 'Generated' ),
            ], 'State', default='p', readonly = True )

    @api.multi
    def generate( self ):
        f = ""
        if self.type == 'ss':
            f = '/simrp/ss.mrx.py'
        if self.type == 'ssrej':
            f = '/simrp/ss.mrx.py'
        if self.type == 'tr':
            f = '/simrp/.mrx.py'
            
        cmd = ""
        with open( tools.config['addons_path'] + f, 'r') as file:
            cmd = file.read()

        exec( cmd )
        self.state = 'g'
        return True
    
    @api.multi
    def download( self ):
        data = {}
        return self.env.ref('simrp.simrp_reportm').report_action(self, data)


    def generate_xlsx_report(self, workbook, data, o):
        #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(data) )
        #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + tools.config['addons_path'] )
        bold = workbook.add_format({'bold': True, 'bg_color': 'yellow'})
        df = workbook.add_format({'num_format': 'dd/mm/yy'})
        nf = workbook.add_format({'num_format': '0.00'})
        nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'green'})

        sheet = workbook.add_worksheet( o.type )
        sheet.write(0, 0, "Report", bold)
        sheet.write(0, 1, o.type)
        sheet.write(1, 0, "From:", bold)
        sheet.write_datetime(1, 1, o.fromdate, df)
        sheet.write(2, 0, "To:", bold)
        sheet.write(2, 1, o.todate, df)
        #read o2m table and make excel as it is

        r = 5
        if o.type in [ 'ss', 'ssrej' ]:
            sheet.write(4, 0, "ss_item", bold)
            sheet.write(4, 1, "ss_itemtype", bold)
            sheet.write(4, 2, "ss_itemcat", bold)
            sheet.write(4, 3, "oprate", bold)
            sheet.write(4, 4, "opstock", bold)
            sheet.write(4, 5, "uom", bold)
            sheet.write(4, 6, "value", bold)
            sheet.write(4, 7, "pogrn", bold)
            sheet.write(4, 8, "sjr", bold)
            sheet.write(4, 9, "wo", bold)
            sheet.write(4, 10, "disp", bold)
            sheet.write(4, 11, "debi", bold)
            sheet.write(4, 12, "pstk", bold)
            sheet.write(4, 13, "scgrn", bold)
            sheet.write(4, 14, "scdc", bold)
            sheet.write(4, 15, "scstk", bold)
            sheet.write(4, 16, "close", bold)
            sheet.write(4, 17, "rate", bold)
            sheet.write(4, 18, "value", bold)
            for rd in o.reportdetails_s:
                sheet.write(r, 0, rd.ss_item )
                sheet.write(r, 1, rd.ss_itemtype )
                sheet.write(r, 2, rd.ss_itemcat )
                sheet.write(r, 3, rd.ss_oprate )
                sheet.write(r, 4, rd.ss_opstock )
                sheet.write(r, 5, rd.ss_itemuom )
                sheet.write(r, 6, rd.ss_opval )
                sheet.write(r, 7, rd.ss_pogrnq )
                sheet.write(r, 8, rd.ss_sjournalq )
                sheet.write(r, 9, rd.ss_womfgq )
                sheet.write(r, 10, rd.ss_dispatchq )
                sheet.write(r, 11, rd.ss_debitq )
                sheet.write(r, 12, rd.ss_physicalstockq )
                sheet.write(r, 13, rd.ss_subcongrnq )
                sheet.write(r, 14, rd.ss_subcondcq )
                sheet.write(r, 15, rd.ss_subconstockq )
                sheet.write(r, 16, rd.ss_closingstock )
                sheet.write(r, 17, rd.ss_clrate )
                sheet.write(r, 18, rd.ss_clvalue )
                r = r + 1

        r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=','simrp.reportm' ) ] )[0]
        r.sudo().report_file = o.type + "AAA"
            
class Reportdetails(models.TransientModel):
    _name = 'simrp.reportdetails'
    
    reportm_ = fields.Many2one( 'report.simrp.reportm', 'Reportm', required = True )
    rmtype = fields.Selection( related='reportm_.type' )
    
    ss_item = fields.Char( 'Ss_item', size = 200 )
    ss_itemcat = fields.Char( 'Ss_itemcat', size = 50 )
    ss_itemtype = fields.Char( 'Ss_itemtype', size = 50 )
    ss_oprate = fields.Float( 'Ss_oprate', digits=(8,2) )
    ss_opval = fields.Float( 'Ss_opval', digits=(8,2) )
    ss_opstock = fields.Float( 'Ss_opstock', digits=(8,2) )
    ss_itemuom = fields.Char( 'Ss_itemuom', size = 20 )
    ss_pogrnq = fields.Float( 'Ss_pogrnq', digits=(8,2) )
    ss_subcongrnq = fields.Float( 'Ss_subcongrnq', digits=(8,2) )
    ss_subcondcq = fields.Float( 'Ss_subcondcq', digits=(8,2) )
    ss_subconstockq = fields.Float( 'Ss_subconstockq', digits=(8,2) )
    ss_sjournalq = fields.Float( 'Ss_sjournalq', digits=(8,2) )
    ss_womfgq = fields.Float( 'Ss_womfgq', digits=(8,2) )
    ss_dispatchq = fields.Float( 'Ss_dispatchq', digits=(8,2) )
    ss_debitq = fields.Float( 'Ss_debitq', digits=(8,2) )
    ss_physicalstockq = fields.Float( 'Ss_physicalstockq', digits=(8,2) )
    ss_closingstock = fields.Float( 'Ss_closingstock', digits=(8,2) )
    ss_clrate = fields.Float( 'Ss_clrate', digits=(8,2) )
    ss_clvalue = fields.Float( 'Ss_clvalue', digits=(8,2) )
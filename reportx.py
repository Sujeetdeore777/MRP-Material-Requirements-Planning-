# -*- coding: utf-8 -*-

import odoo.tools as tools
import datetime
from odoo import api, fields, models
import base64, json
import logging
_logger = logging.getLogger(__name__)
from dateutil.rrule import rrule, MONTHLY, DAILY
from . import shiftinfo
from odoo.addons.simrp.accentry import Account

    
class Salereport(models.TransientModel):
    _name = 'simrp.salereport'
    _inherit = 'report.report_xlsx.abstract'

    fromdate = fields.Date( 'From Date', default=lambda self: fields.Date.today() )
    todate = fields.Date( 'To Date', default=lambda self: fields.Date.today() )
    period = fields.Selection( [
            ( 'internalanalysis', 'Internal Analysis' ),
            ( 'netsale', 'Net Sales' ),
            ], 'Report Type', default= None, required = True )
    party_ = fields.Many2one( 'simrp.party', 'Party Account', readonly = True )
    item_ = fields.Many2one( 'simrp.item', 'Items', readonly = True )
    reporthtml = fields.Text( 'Report HTML', readonly = True, default='{}' )
    reporthtm = fields.Text( 'Report HTML', readonly = True, default='{}' )
    @api.onchange('period')
    
    def generate(self):
        for o in self:
            custmaster = { }
            monthlist = [dt.strftime("%b-%y") for dt in rrule(MONTHLY, dtstart=self.fromdate, until=self.todate)]
            # _logger.info(monthlist)
            invoices = self.env[ 'simrp.invoice' ].search( [ ('invdate', '>=', o.fromdate), ('invdate', '<=', o.todate)] )
            party = self.env[ 'simrp.party' ].search( [ ('associate', '=', 'cust') , ('category', '=', 't') ] )
            item = self.env[ 'simrp.item' ].search( [ ('useinsales', '=', True) ] )
            # _logger.info( item )
            q1 = { 'Apr' : 0, 'May' : 0 , 'Jun' : 0}
            q2 = { 'Jul' : 0, 'Aug' : 0 , 'Sep' : 0}
            q3 = { 'Oct' : 0, 'Nov' : 0 , 'Dec' : 0}
            q4 = { 'Jan' : 0, 'Feb' : 0 , 'Mar' : 0}
            cnt = 0
            for v in party:
                custmaster[v.name] = {}
                for m in monthlist:
                    # custmaster[v.name][m] = { 'month' : m , 'sale': 0}
                    custmaster[v.name][m] = { 'sale': 0 }
            
            for p in party:
                for sl in invoices:
                    pid = sl.party_.id
                    if pid == p.id:
                        custmaster[sl.party_.name][sl.invdate.strftime( '%b-%y' ) ]['sale'] = round((custmaster[sl.party_.name][sl.invdate.strftime( '%b-%y' ) ]['sale'] + sl.basicamt), 0)
                        if sl.invdate.strftime( '%b' ) in q1.keys():
                            q1[sl.invdate.strftime( '%b' )] = q1[sl.invdate.strftime( '%b' )] + (sl.basicamt)
                        if sl.invdate.strftime( '%b' ) in q2.keys():
                            q2[sl.invdate.strftime( '%b' )] = q2[sl.invdate.strftime( '%b' )] + (sl.basicamt)
                        if sl.invdate.strftime( '%b' ) in q3.keys():
                            q3[sl.invdate.strftime( '%b' )] = q3[sl.invdate.strftime( '%b' )] + (sl.basicamt)
                        if sl.invdate.strftime( '%b' ) in q4.keys():
                            q4[sl.invdate.strftime( '%b' )] = q4[sl.invdate.strftime( '%b' )] + (sl.basicamt)
                        
            dic = {
                'custmaster': custmaster,
                }
            d = {
                'q1' : q1,
                'q2' : q2,
                'q3' : q3,
                'q4' : q4
            }
        _logger.info(dic)
        o.reporthtml = json.dumps(dic)
        o.reporthtm = json.dumps(d)

    def reportprod( self ):
        rp = self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        cmd = ""
        with open( rp + '/simrp/salereporthtml.py', 'r') as file:
            cmd = file.read()
        for o in self:
            exec( cmd )
            _logger.info( 'SSSSSSSSSSSSSSSSSSSSSSSS ' + o.reporthtml )
            _logger.info( 'SSSSSSSSSSSSSSSSSSSSSSSS ' + o.reporthtm )
            
    def downloadreport( self ):
        data = {}
        return self.env.ref('simrp.simrp_salereport').report_action(self, data)
        
    def getreportpath( self ):
        return self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        
    def generate_xlsx_report(self, workbook, data, o):
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(data) )
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + tools.config['addons_path'] )
        _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + o._name )

        f = '/simrp/salessummary.rx.py'
            
        cmd = ""
        with open( self.getreportpath() + f, 'r') as file:
            cmd = file.read()
            _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )

        exec( cmd )
        r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
        r.sudo().report_file = '_' + o.fromdate.strftime( '%d%m%Y' ) + '_' + o.todate.strftime( '%d%m%Y' )

class Reportx(models.TransientModel):
    _name = 'report.simrp.reportx'
    _inherit = 'report.report_xlsx.abstract'

    fromdate = fields.Date( 'From Date', default=lambda self: fields.Date.today() )
    todate = fields.Date( 'To Date', default=lambda self: fields.Date.today() )
    date = fields.Date( 'Date', default=lambda self: fields.Date.today() )
    trainee_day = fields.Integer( 'Trainee Days', default=30 )
    Reissue_interval = fields.Integer( 'Reissue Interval', default=365 )
    type = fields.Selection( [
            ( 'eawv', 'Employee Attendance-Work Variance' ),
            ( 'att', 'Attendance Report' ),
            ( 'gstr1', 'GSTR1 Sale Report' ),
            ( 'gstr3b', 'GSTR3B Purchase Report' ),
            ( 'clbal', 'Closing balance report 2019-20' ),
            ( 'payable', 'Payables Report' ),
            ( 'purdn', 'Purchase Record Rej Check' ),
            ( 'uniform', 'Uniform Report' ),            
            ( 'tl', 'Financial Report' ),
            ( 'salesr', 'Sales_report' ),
            ], 'Report Type', default='payable', required=True )
    # ignorezero = fields.Boolean( 'Ignore Zero entries' )
    
    csv = fields.Text( 'CSV', readonly=True )
    json = fields.Binary( 'Download 1' )
    storename = fields.Char( 'Name 1' )
    json1 = fields.Binary( 'Download 2' )
    storename1 = fields.Char( 'Name 2' )
    json2 = fields.Binary( 'Download 3' )
    storename2 = fields.Char( 'Name 3' )
    json3 = fields.Binary( 'Download 4' )
    storename3 = fields.Char( 'Name 4' )
    json4 = fields.Binary( 'Download 5' )
    storename4 = fields.Char( 'Name 5' )
    htest = fields.Text( 'Htest' )
    htestcom = fields.Html( compute='_htestcom' )
    
    def _htestcom( self ):
        for o in self:
            o.htestcom = o.htest
    

    def getreportpath( self ):
        return self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
    
    # def setjson( self ):
        # f = ""
        # if self.type == 'gstr1':
            #f = '/simrp/gstr1.json.py'            
        # if f != "":
            # cmd = ""
            # with open( self.getreportpath() + f, 'r') as file:
                # cmd = file.read()
            # exec( cmd )
    
    @api.multi
    def generate( self ):
        data = {}
        return self.env.ref('simrp.simrp_reportx').report_action(self, data)

    @api.multi
    def loadcsv( self ):
        f = ""
        if self.type == 'purdn':
            f = '/simrp/purdn.csv.py'
        if self.type == 'gstr1':
            f = '/simrp/gstr1.csv.py'
            # self.csv = self.getcsv()
            
        if f != "":
            cmd = ""
            with open( self.getreportpath() + f, 'r') as file:
                cmd = file.read()
            exec( cmd )
    
    
    # @api.model
    # def getcsv( o ):
        # global s
        # s = ""

        # dr = o.env['simrp.dispatch'].search( [ ( 'invdate','>=',o.fromdate ), ( 'invdate','<=',o.todate ), ( 'state','=','i' ) ] )
        # s = 'Import B2B Section\n\n'
        # s = s + "GSTIN/UIN of Recipient,Receiver Name,Invoice Number,Invoice date,Invoice Value,Place Of Supply,Reverse Charge,Invoice Type,E-Commerce GSTIN,Rate,Applicable % of Tax Rate,Taxable Value,Cess Amount\n"
        
        # hsnd = {}
        # for d in dr:
            # bval = round( d.saleorder_.rate * d.okoutqty, 2 )
            # dtax = d.saleorder_.taxscheme_.compute( bval )
            # s = s + d.party_.gstno + ',' + d.party_.name + ','
            # s = s + d.invno + ',' + d.invdate.strftime( '%d-%b-%y' ) + ',' + str( round( d.invamt, 2 ) ) + ','
            # s = s + d.party_.state_.gstname() + ',N,Regular,,'
            # s = s + str( dtax[ 'taxclass' ][ 'totalrate' ] ) + ',,' + str( bval ) + ',\n'
            
            # hsncode = d.item_.hsnsac
            # if hsncode not in hsnd.keys():
                # hsnd[ hsncode ] = { 'uqc': d.item_.uom_.gstr1code, 'tq': 0, 'tv': 0, 'bv': 0, 'igst': 0, 'cgst': 0, 'sgst': 0 }
                
            # hsnd[ hsncode ][ 'tq' ] = hsnd[ hsncode ][ 'tq' ] + d.okoutqty
            # hsnd[ hsncode ][ 'tv' ] = hsnd[ hsncode ][ 'tv' ] + round( d.invamt, 2 )
            # hsnd[ hsncode ][ 'bv' ] = hsnd[ hsncode ][ 'bv' ] + bval
            # hsnd[ hsncode ][ 'igst' ] = hsnd[ hsncode ][ 'igst' ] + dtax[ 'taxclass' ][ 'igst' ]
            # hsnd[ hsncode ][ 'cgst' ] = hsnd[ hsncode ][ 'cgst' ] + dtax[ 'taxclass' ][ 'cgst' ]
            # hsnd[ hsncode ][ 'sgst' ] = hsnd[ hsncode ][ 'sgst' ] + dtax[ 'taxclass' ][ 'sgst' ]

        # s = s + '\n\nImport HSN Section\n\n'
        # s = s + 'HSN,Description,UQC,Total Quantity,Total Value,Taxable Value,Integrated Tax Amount,Central Tax Amount,State/UT Tax Amount,Cess Amount\n'
        
        # for h in hsnd.keys():
            # if h:
                # s = s + h + ',,'
                # s = s + hsnd[ h ][ 'uqc' ] + ',' + str( hsnd[ h ][ 'tq' ] ) + ',' + str( hsnd[ h ][ 'tv' ] )
                # s = s + ',' + str( hsnd[ h ][ 'bv' ] ) + ',' + str( round( hsnd[ h ][ 'igst' ], 2 ) ) + ',' + str( round( hsnd[ h ][ 'cgst' ], 2 ) ) + ',' + str( round( hsnd[ h ][ 'sgst' ], 2 ) ) + ',\n'

        # s = s + '\n\nImport Docs Section\n\n'
        # s = s + 'Pending\n'
                
        # return s
    
    def generate_xlsx_report(self, workbook, data, o):
        #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(data) )
        #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + tools.config['addons_path'] )

        bold = workbook.add_format({'bold': True, 'bg_color': 'yellow'})

        f = ""
        if o.type == 'eawv':
            f = '/simrp/eawv.rx.py'
        if o.type == 'att':
            f = '/simrp/att.rx.py'
        if o.type == 'gstr1':
            f = '/simrp/gstr1.rx.py'
        if o.type == 'gstr3b':
            f = '/simrp/gstr3b.rx.py'
        if o.type == 'clbal':
            f = '/simrp/clbal.rx.py'
        if o.type == 'payable':
            f = '/simrp/payable.rx.py'
        if o.type == 'uniform':
            f = '/simrp/uniform.rx.py'
            
        if o.type == 'salesr':
            f = '/simrp/salesr.rx.py'
           
           
           
        if o.type == 'tl':
            f = '/simrp/tl.rx.py'
            
        if f != "":
            cmd = ""
            with open( self.getreportpath() + f, 'r') as file:
            #with open( 'C:\\Kmain\\dev\\odoo12addons\\' + f, 'r') as file:
            
                cmd = file.read()
                _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + cmd )

            exec( cmd )
            r = self.env['ir.actions.report'].sudo().search( [ ( 'report_name','=',o._name ) ] )[0]
            r.sudo().report_file = o.type + "AAA"
            
    @api.model        
    def addPLBSdetails( self, nfg, nfr, nf,  bold, sheetf, sheet, o, r, bs, d, at, sfr, sfc, sfc1, dm, oponly=False, clonly=False ):
        # nfg = number format green
        # nfr = number format red
        # nf = number format
        # bold = bold format
        # sheetf, sheet
        
        # bs :: true = show opening and closing
        # d :: [ 1 = debtors ][ -1 = creditors ][ 0 = any ]
        # r = next row on trial balance sheet
        # dm (debit side multiplier for pnl) 1 or -1

        # _logger.info( '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2' )
        # _logger.info( self.ignorezero )
        
        if oponly or clonly:
            pass
        else:
            sheet.write(r, 0, at[ 1 ], bold )
            r = r+1
        ttotal = 0
        accs = self.env['simrp.account'].search( [ ( 'type','=',at[ 0 ] ) ], order='type,name' )
        for acc in accs:
            odr = 0
            ocr = 0
            pdr = 0
            pcr = 0
            erpbilladj = 0
            acclines = self.env['simrp.accline'].search( [ ( 'account_', '=', acc.id ), ('docdate', '<=', o.todate ) ] )
            for ae in acclines:
                erpbilladj = erpbilladj + ae.baladjAmount
                if ae.docdate < o.fromdate:
                    odr = odr + ae.amountdr
                    ocr = ocr + ae.amountcr
                else:
                    pdr = pdr + ae.amountdr
                    pcr = pcr + ae.amountcr
            cdr = odr + pdr
            ccr = ocr + pcr
            showrow = True
            # if self.ignorezero:
            # if True:
                # if abs( ccr - cdr ) < 0.001:
                    # showrow = False
                # else:
                    # _logger.info( acc.name + ' ' + str( ccr ) + ' ' + str( cdr ) )
            if showrow:
                if oponly:
                    ttotal = ttotal + odr - ocr
                elif clonly:
                    ttotal = ttotal + cdr - ccr
                else:
                    if ( bs and ( not ( ( odr - ocr == 0 ) and ( pdr == 0 ) and ( pcr == 0 ) ) ) ) or ( (not bs) and ( not ( ( pdr == 0 ) and ( pcr == 0 ) ) ) ):
                        # if ( odr != 0 ):
                            # sheet.write(r, 1, odr, nf )
                        # if ( ocr != 0 ):
                            # sheet.write(r, 2, ocr, nf )
                        
                        if ( ( d == 1 ) and ( cdr - ccr > 0 ) ) or ( ( d == -1 ) and ( cdr - ccr <= 0 ) ) or ( d == 0 ):
                            sheet.write(r, 0, acc.name)
                            if bs:
                                if ( odr - ocr > 0 ):
                                    sheet.write(r, 3, odr - ocr, nfg )
                                if ( odr - ocr < 0 ):
                                    sheet.write(r, 3, odr - ocr, nfr )
                                if ( cdr - ccr > 0 ):
                                    sheet.write(r, 9, cdr - ccr, nfg )
                                if ( cdr - ccr < 0 ):
                                    sheet.write(r, 9, cdr - ccr, nfr )
                                    
                                sheet.write(r, 11, erpbilladj, nf )
                                sheet.write(r, 12, erpbilladj - (cdr-ccr), nf )
                                    
                                ttotal = ttotal + cdr - ccr
                            else:
                                ttotal = ttotal + pdr - pcr

                            if ( pdr != 0 ):
                                sheet.write(r, 4, pdr, nf )
                            if ( pcr != 0 ):
                                sheet.write(r, 5, pcr, nf )
                            if ( pdr - pcr > 0 ):
                                sheet.write(r, 6, pdr - pcr, nfg )
                            if ( pdr - pcr < 0 ):
                                sheet.write(r, 6, pdr - pcr, nfr )
                            # if ( cdr != 0 ):
                                # sheet.write(r, 7, cdr, nf )
                            # if ( ccr != 0 ):
                                # sheet.write(r, 8, ccr, nf )
                            r = r + 1
        r = r + 1
        
        #if not bs:
        ttotal = ttotal * dm
        sheetf.write(sfr, sfc, at[ 1 ] )
        sheetf.write(sfr, sfc1, ttotal, (nfr if ( ttotal < 0 ) else nfg) )
        
        return r
        
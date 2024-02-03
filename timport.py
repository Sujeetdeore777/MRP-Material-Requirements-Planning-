# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

import xlrd, base64

class Timport(models.TransientModel):
    _name = 'simrp.timport'

    ifile = fields.Binary( 'Import File:', required = True )
    ifilename = fields.Char( 'File Name' )

    fundaccount_ = fields.Many2one( 'simrp.account', 'Fund Account' )
    log = fields.Text( 'Log', readonly = True )
    trial = fields.Boolean( 'Trial', default=True )
    
    def bankimport( self ):
        if not self.fundaccount_:
            raise exceptions.UserError( 'Select Fund Account' )
        s = self.fundaccount_.name
        fano = s[ s.find( '[' ) + 1:s.find( ']' ) ]
        if fano not in self.ifilename:
            raise exceptions.UserError( 'File name doesnt contain fund account no.. Also ensure ledger name with account no in []' )
        wb = xlrd.open_workbook(file_contents = base64.decodestring( self.ifile ))
        sheet = wb.sheets()[0]
        log = ''
        for row in range( 1, sheet.nrows ):
            td = datetime.datetime.strptime( sheet.cell(row, 0).value, '%d/%m/%Y %H:%M:%S').date()
            bdes = sheet.cell(row, 1).value
            amt = sheet.cell(row, 2).value
            crdr = sheet.cell(row, 3).value
            bref = sheet.cell(row, 4).value
            cb = sheet.cell(row, 7).value

            log = log + sheet.cell(row, 0).value + ' [' + str( amt ) + '] ' + bdes + ' '
            
            dft = self.env[ 'simrp.fundtransaction' ].search( [ ('ftdate','=',td), ('amount','=',amt), ('statementid','ilike',bdes)  ] )
            if dft:
                log = log + '<b>[DUPLICATE]</b><br/>'
            else:
                if not self.trial:
                    self.env[ 'simrp.fundtransaction' ].create( {
                        'ftdate': td.strftime( '%Y-%m-%d' ),
                        # 'ftdate': td.strftime( '%d/%m/%Y' ),
                        'bdes': bdes,
                        'bref': bref,
                        'wa': amt if ( crdr == 'D' ) else 0,
                        'da': amt if ( crdr == 'C' ) else 0,
                        'cb': cb,
                        'fundaccount_': self.fundaccount_.id,
                    } )
                    log = log + '<font color="green"><b>[OK]</b></font><br/>'
                else:
                    log = log + '<font color="green"><b>[OK-TRIAL]</b></font><br/>'
        self.log = log
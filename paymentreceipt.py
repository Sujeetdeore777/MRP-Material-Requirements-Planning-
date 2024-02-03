import datetime, time
import calendar
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)

class PaymentReceipt(models.TransientModel):
    _name = 'simrp.paymentreceipt'

    party_ = fields.Many2one( 'simrp.account', 'Party', required = True )
    date = fields.Date( 'Date',default=lambda self: fields.Date.today(), required = True )
    fundaccount_ = fields.Many2one( 'simrp.account', 'Fund Account')
    chq_no = fields.Char( 'Cheque No.', required = True)
    chq_amt = fields.Float( 'Cheque Amount',digits=(8,2), required = True, default=0)
    uti_no = fields.Char( 'UTI No.')
    tcustpaymentrecords_s = fields.One2many( 'simrp.tcustpaymentrecords', 'paymentreceipt_', 'All Records')
    state = fields.Selection( [
            ( 's', 'Start' ),
            ( 'l', 'Load' ),
            ( 'c', 'Confirmed' ),
            ( 'p', 'Processed' ),
            ], 'State', default='s', readonly = True )

    @api.multi
    @api.depends('party_')
    def load(self):
        self.state = 'l'
        for rec in self:
            acclines = self.env['simrp.accline'].search( [ ( 'account_', '=', rec.party_.id ), ( 'baladjAmount', '!=', 0 ) ], order='amountdr desc, docdate' )
            for d in acclines:
                if not d.ref_:
                    transaction = " "
                else:
                    transaction = d.ref_.name
                line = self.env[ 'simrp.tcustpaymentrecords' ].create( {
                    'paymentreceipt_': self.id,
                    'accline_': d.id,
                    'tran': transaction,
                } )
            return True

    @api.multi
    def confirm(self):
        self.state = 'c'
        for rec in self:
            _logger.info("********************")
            line = self.env[ 'simrp.fundtransaction' ].create( {
                'fundaccount_': rec.fundaccount_.id,
                'amount': rec.chq_amt,
                'ftdate': rec.date.strftime( '%d/%m/%Y' ),
                'party_': rec.party_.id,
                'des': rec.chq_no,
                })
            line.submit()
            return True

class TPaymentTreetable(models.TransientModel):
    _name = 'simrp.tcustpaymentrecords'

    paymentreceipt_ = fields.Many2one( 'simrp.paymentreceipt', 'payment receipt', required=True)
    accline_ = fields.Many2one( 'simrp.accline', 'Accline',readonly = True)
    tran = fields.Char( 'Trasaction',readonly = True )
    doc_date = fields.Date( related='accline_.docdate' )
    doc_dr = fields.Float(related='accline_.amountdr')
    doc_cr = fields.Float(related='accline_.amountcr')
    bal_amt = fields.Float( related='accline_.baladjAmount' )
    check = fields.Boolean(default=False)


import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class cash(models.Model):
    _name = 'simrp.cash'

    name = fields.Char( 'Tx No', readonly = True ,copy=False,select=True, default='New' )
    date = fields.Date( 'Date',default=lambda self: fields.Date.today(), readonly = True )
    cash_ledger_acc_in = fields.Many2one( 'simrp.account','Cash Ledger Acc In')
    out_amount = fields.Float( 'Out Amount', size = 15 ,required = True )
    exp_head = fields.Many2one( 'simrp.account','Expense Head' )
    cash_ledger_acc_out = fields.Many2one( 'simrp.account','Cash Ledger Acc Out', required = True )
    Description = fields.Char( 'Description', size = 50, required = True )
    state = fields.Selection( [
            ( 'draft', 'Draft' ),
            ( 'submit', 'Submit' ),
            ( 'approved', 'Approved' ),
            ], 'state', default='draft', required = True )
    type = fields.Selection( [
            ( 'cash_tran', 'Cash Transfer' ),
            ( 'cash_exp', 'Cash Expenditure' ),
            ], 'type', default='cash_exp', required = True )
    accline_s = fields.One2many( 'simrp.accline', 'cash_', 'Account Postings', readonly = True )

    @api.multi
    def apprv(self):
        self.env[ 'simrp.accentry' ].browse( 1 ).initCash( self.id, self.type, self.out_amount, self.cash_ledger_acc_out, self.cash_ledger_acc_in, self.exp_head )
        self.update({'state':'approved'})
        return True 

    @api.model
    def create(self, vals):
       vals['name'] = self.env['ir.sequence'].get('simrp.cash')
       return super().create(vals)

    def submit(self):
      for r in self:
        if r.type == 'cash_tran':
            if r.cash_ledger_acc_out == r.cash_ledger_acc_in:
                raise exceptions.UserError("Out account & In account Both Are Same.")
        else:
            r.cash_ledger_acc_in = False
        if r.out_amount <= 0:
            raise exceptions.UserError("Out amount is incorrect")
        self.update({'state':'submit'})
        return True
        
    def unlink( self ):
        for o in self:
            for aline in o.accline_s:
                aline.delete()
        return super().unlink()
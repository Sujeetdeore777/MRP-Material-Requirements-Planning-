
import datetime, time, json
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import shiftinfo

class EmpAdvance(models.Model):
    _name = 'simrp.empadvance'

    employee_ = fields.Many2one( 'simrp.employee', 'Employee', required = True )
    docdate = fields.Date( 'Transaction Date',default=lambda self: fields.Date.today(), required = True )
    salaryrecord_ = fields.Many2one( 'simrp.salaryrecord', 'Linked Salary Record', readonly = True )    
    monthempsalary_ = fields.Many2one( related='salaryrecord_.monthempsalary_' )

    amount = fields.Float( 'Amount (+/-)', required = True )
    des = fields.Char( 'Remarks', size = 200 )

    # @api.model
    # def create(self, vals):
        # # vals['name'] = self.env['ir.sequence'].next_by_code('simrp.transporttrip')
        # raise exceptions.UserError( json.dumps( self.env.context ) )

        # return super(EmpAdvance, self).create(vals)

# class Advance(models.Model):
    # _name = 'simrp.advance'

    # employee_ = fields.Many2one( 'simrp.employee', 'Employee', required = True )
    # date = fields.Date( 'Requested Date',default=lambda self: fields.Date.today(), readonly = True )
    # payment_date = fields.Date( 'Payment Date',default=lambda self: fields.Date.today(), required = True )
    # close_date = fields.Date( 'Close Date')
    # amount = fields.Float( 'Amount', required = True )
    # bal_amount = fields.Float( 'Balance Amount', digits=(8,2), compute='bal_amt', store=True )
    # reason = fields.Char( 'Reason', size = 100, required = False )
    # deduction_argmnt = fields.Char( 'Deduction Agreement', size = 100, required = False )
    # advancededuction_s = fields.One2many( 'simrp.advancededuction', 'advance_', 'Deduction' )
    # status = fields.Selection( [
            # ( 'o', 'Open' ),
            # ( 'c', 'Closed' ),
            # ], 'Status', default='o', required = True )

    # @api.multi
    # def close(self):
        # self.update({'status':'c'})
        # self.update({'close_date':fields.Date.today()})
        # return True
    
    # @api.multi
    # @api.depends('amount','advancededuction_s.amount')
    # def bal_amt(self):
        # for o in self:
            # sum = 0
            # for i in o.advancededuction_s:
                # sum = sum + i.amount
            # o.bal_amount = o.amount - sum

# class AdvanceDeduction(models.Model):
    # _name = 'simrp.advancededuction'

    # advance_ = fields.Many2one( 'simrp.advance', 'Advance', required = True )
    # date = fields.Date( ' Date',default=lambda self: fields.Date.today(), required = True )
    # amount = fields.Float( 'Amount', required = True )
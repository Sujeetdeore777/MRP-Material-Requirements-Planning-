import datetime, time, json
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Exportinv(models.Model):
    _name = 'simrp.exportinv'
    
    name = fields.Char( 'Export Invoice No.', size = 40, required = True )
    edate = fields.Date( 'Export Invoice Date', default=lambda self: fields.Date.today(), required = True )
    
    pono = fields.Char( 'PO No.', size = 100 )
    podate = fields.Date( 'PO date' )
    
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    saleaccount_ = fields.Many2one( 'simrp.account', 'Sale Account', required = True )
    
    exportdetails_s = fields.One2many( 'simrp.exportdetails', 'exportinv_', 'Exportdetails' )
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 's', 'Submit' ),
            ( 'r', 'Recorded' ),
            ], 'State', default='d', readonly = True )
            
    amount = fields.Float( 'Amount', digits=(8,2), compute='_amount' )
    currency = fields.Char( 'Currency', size = 20, required = True, default='EURO' )
    sbconvrate = fields.Float( 'INR rate in SB', digits=(8,2), required = True )
    inramount = fields.Float( 'INR Amount', digits=(8,2), compute='_amount' )

    sbno = fields.Char( 'Shipping Bill No.', size = 100 )
    sbdate = fields.Date( 'SB date' )
    insno = fields.Char( 'Insurance Policy No.', size = 100 )
    insdate = fields.Date( 'IP date' )
    
    transportagency = fields.Char( 'Transport Agency Name', size = 100 )
    awbno = fields.Char( 'Transport AWB No', size = 100 )
    
    des = fields.Text( 'Other Remarks' )
    
    accline_s = fields.One2many( 'simrp.accline', 'exportinv_', 'Acc lines', readonly = True )


    @api.depends( 'exportdetails_s', 'exportdetails_s.qty', 'exportdetails_s.rate', 'sbconvrate' )
    def _amount( self ):
        for o in self:
            a = 0
            for ed in o.exportdetails_s:
                a = a + ed.amount
            o.amount = a
            o.inramount = o.amount * o.sbconvrate

    def submit( self ):
        if ( not self.sbno ) or ( not self.sbdate ):
            raise exceptions.UserError('Enter SB details')
        if ( not self.insno ) or ( not self.insdate ):
            raise exceptions.UserError('Enter Insurance details')
        if ( not self.transportagency ) or ( not self.awbno ):
            raise exceptions.UserError('Enter Transport Agency details')
        self.state = 's'

    def draft( self ):
        self.state = 'd'

    def record(self):
        self.env[ 'simrp.accentry' ].browse( 1 ).initEXP( self.id, self.saleaccount_, self.party_.account_, self.inramount )
        self.state = 'r'

class Exportdetails(models.Model):
    _name = 'simrp.exportdetails'
    
    exportinv_ = fields.Many2one( 'simrp.exportinv', 'Exportinv', required = True )
    
    des = fields.Char( 'Description', size = 500, required = True )
    qty = fields.Float( 'Qty', digits=(8,2), required = True )
    rate = fields.Float( 'Rate', digits=(8,2), required = True )
    amount = fields.Float( 'Amount', digits=(8,2), compute='_amount' )
    
    @api.depends( 'qty', 'rate' )
    def _amount( self ):
        for o in self:
            o.amount = o.qty * o.rate
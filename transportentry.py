import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Transporttrip(models.Model):
    _name = 'simrp.transporttrip'

    name = fields.Char( ' Code.', size = 50, readonly = True )
    date = fields.Date( ' Date', default=lambda self: fields.Date.today(), required = True )
    party_ = fields.Many2one( 'simrp.party', 'Transporter Name', required = True)
    tripdetail_s = fields.One2many( 'simrp.tripdetail', 'transporttrip_', 'Transport Trip' )
    amount = fields.Float( 'Basic Amount', digits=(8,2), compute='basicamount', store = True )
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 's', 'Submit' ),
            ( 'c', 'Confirm' ),
            ], 'State', readonly = True, default='d' )
    starttime = fields.Selection( [
            ( '7', '07:00' ),
            ( '8', '08:00' ),
            ( '9', '09:00' ),
            ( '10', '10:00' ),
            ( '11', '11:00' ),
            ( '12', '12:00' ),
            ( '13', '13:00' ),
            ( '14', '14:00' ),
            ( '15', '15:00' ),
            ( '16', '16:00' ),
            ( '17', '17:00' ),
            ( '18', '18:00' ),
            ( '19', '19:00' ),
            ( '20', '20:00' ),
            ( '21', '21:00' ),
            ( '22', '22:00' ),
            ( '23', '23:00' ),
            ], 'Trip Start Time', required = True, default='10' )
    accline_s = fields.One2many( 'simrp.accline', 'transporttrip_', 'Account Postings', readonly = True )

    _order = 'id desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.transporttrip')
        return super(Transporttrip, self).create(vals)

    @api.multi
    @api.depends( 'tripdetail_s.location','tripdetail_s.rate' )
    def basicamount(self):
        for rec in self:
          amt = 0
          for o in rec.tripdetail_s:
            amt = amt + o.rate
        rec.amount = amt

    @api.multi
    def submit(self):
        #self.check()
        self.state = 's'
        return True

    @api.multi
    def accept(self):
        dr = self.env['simrp.account'].search( [ ( 'code','=','LTRP' ) ])
        if not dr:
            raise exceptions.UserError("Local Transport Account - Auto Code LTRP, not defined. Cannot proceed")
        
        self.env[ 'simrp.accentry' ].browse( 1 ).initTransport( self.id, self.party_.account_, self.amount, dr[0] )
        self.state = 'c'
        self.env[ 'simrp.auditlog' ].log( self, 'Trip: ', self.read( [ 'name', 'party_', 'starttime', 'amount' ] )[0], False, False )
        
        return True



class Tripdetail(models.Model):
    _name = 'simrp.tripdetail'

    transporttrip_ = fields.Many2one( 'simrp.transporttrip', 'Transporter Entry Code', required = True)
    tadetail_ = fields.Many2one( 'simrp.tadetail', 'Transport type', required = True)
    location = fields.Char( 'Trip Desc', size = 100, required = True )
    rate = fields.Integer( 'Amount', default=0, readonly = True )

    @api.onchange( 'tadetail_' )
    def check(self):
        self.rate = self.tadetail_.rate

    @api.model
    def create(self, vals):
        vals[ 'rate'] = self.env[ 'simrp.tadetail' ].browse( vals['tadetail_'] ).rate
        return super(Tripdetail, self).create(vals)

    @api.model
    def write(self, vals):
        if 'tadetail_' in vals.keys():
            vals[ 'rate'] = self.env[ 'simrp.tadetail' ].browse( vals['tadetail_'] ).rate
        return super(Tripdetail, self).write(vals)


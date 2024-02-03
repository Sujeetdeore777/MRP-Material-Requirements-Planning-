import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class AdvGRN(models.Model):
    _name = 'simrp.advancegrn'

    name = fields.Char( 'Adv GRN Code.', size = 20, readonly = True )
    des = fields.Char( 'Notes', size = 200, required = False )
    agrndate = fields.Date( 'Adv GRN Date', default=lambda self: fields.Date.today(), readonly = True )
    agrndatetime = fields.Datetime( 'Adv GRN Date', default=lambda self: fields.datetime.now(), readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    item_ = fields.Many2one( 'simrp.item', 'Items', required = True )
    hsnsac = fields.Char( related='item_.hsnsac' )
    
    receiveqty = fields.Float( 'Received Quantity', default=0, required = True )
    rate = fields.Float( 'Rate/Unit', default=0, required = True )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax scheme', required = True )
    amount = fields.Float( 'Basic Amount', digits=(8,2), compute='_amt',store = True )
    state = fields.Selection( [
            ( 'r', 'Received' ),
            ( 'acc', 'Accounted' ),
            ( 'c', 'Cancelled' ),
            ], 'State', readonly = True, default='r' )
    purchase_ = fields.Many2one( 'simrp.purchase', 'Purchase Entry:', readonly = True, ondelete='set null' )
    userid = fields.Char("User ID",default=lambda self: self.env.user.name)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.advancegrn')
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'MiscGRN: ' + o.item_.name, o.read( [ 'name', 'party_', 'receiveqty', 'rate', 'taxscheme_', 'amount' ] )[ 0 ], False, False )
        return o

    @api.multi
    @api.depends('rate','receiveqty')
    def _amt(self):
        self.amount = self.receiveqty * self.rate

    def cancel(self):
        if self.purchase_:
            raise exceptions.UserError( 'Already accounted. Cannot Cancel' )
        self.state = 'c'
        return True

# class TAdvGRN(models.TransientModel):
    # _name = 'simrp.tadvancegrn'

    # des = fields.Char( 'Notes', size = 200, required = False )
    # agrndate = fields.Date( 'Adv GRN Date', default=lambda self: fields.Date.today(), readonly = True )
    # agrndatetime = fields.Datetime( 'Adv GRN Date', default=lambda self: fields.datetime.now(), readonly = True )
    # party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    # item_ = fields.Many2one( 'simrp.item', 'Items', required = True )
    # receiveqty = fields.Float( 'Received Quantity', default=0, required = True )
    # rate = fields.Float( 'Rate/Unit', default=0, required = True )
    # taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax scheme', required = True )

    # @api.multi
    # def createline(self):
        # line = self.env[ 'simrp.advancegrn' ].create( {
            # 'des': self.des,
            # 'agrndate': self.agrndate,
            # 'agrndatetime': self.agrndatetime,
            # 'party_': self.party_.id,
            # 'item_': self.item_.id,
            # 'receiveqty': self.receiveqty,
            # 'rate': self.rate,
            # 'taxscheme_': self.taxscheme_.id,
        # } )
        # return True

# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Stock(models.Model):
    _name = 'simrp.stock'
    
    ref = fields.Reference( [
            ('simrp.grn', 'GRN'), 
            ('simrp.dispatch', 'Dispatch'),
            ('simrp.subcondc', 'Subcon DC'),
            ('simrp.debit', 'Debit'),
            ('simrp.sjournal', 'Stock Journal'),
            ('simrp.physicalstock', 'Physical Stock'),
            ('simrp.openingstock', 'Opening Stock'),
            ('simrp.womfg', 'WO Manufacturing'),
            ], string='Document Ref', readonly = True )  
    recdate = fields.Datetime( 'Time', readonly = True, default=lambda self: fields.Datetime.now() )
            
    party_ = fields.Many2one( 'simrp.party', 'Party' )
    item_ = fields.Many2one('simrp.item', 'Item' )
    
    itemtype = fields.Selection( related='item_.type', string='Item Type' )
    itemuom_ = fields.Many2one( related='item_.uom_' ) 
    
    okinqty = fields.Float( 'Ok In', digits=(8,2), default=0 )
    rejinqty = fields.Float( 'Rej In', digits=(8,2), default=0 )
    okoutqty = fields.Float( 'Ok Out', digits=(8,2), default=0 )
    rejoutqty = fields.Float( 'Rej Out', digits=(8,2), default=0 )
    
    _order = 'recdate desc'
    
    @api.model
    def initStock( self, item_, refm, refid, party_ ):
        s = self.sudo()
        if item_:
            s.item_ = item_.id
        if party_:
            s.party_ = party_.id
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + refm + ", " + str(refid) )
        s.ref = '%s,%s' % ( refm, refid )

        
class Physicalstock(models.Model):
    _name = 'simrp.physicalstock'
    
    name = fields.Char( 'Code', size = 20, default='<draft>', readonly = True )
    pdate = fields.Datetime( 'Date', default=lambda self: fields.Datetime.now(), readonly = True )
    
    item_ = fields.Many2one('simrp.item', 'Item' )
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'a', 'Approve' ),
            ], 'State', readonly = True,default='d' )
    
    erpok = fields.Float( 'Erp ok', digits=(8,2), compute='_erpok' )
    erprej = fields.Float( 'Erp Rej', digits=(8,2), compute='_erprej' )
    okqty = fields.Float( 'Ok Stk', digits=(8,2) )
    rejqty = fields.Float( 'Rej Stk', digits=(8,2) )
    
    okadj = fields.Float( 'Ok Adj', digits=(8,2), readonly = True )
    rejadj = fields.Float( 'Rej Adj', digits=(8,2), readonly = True )
    stock_ = fields.Many2one( 'simrp.stock', 'Stock', readonly = True )
    

    @api.multi
    @api.depends( 'item_', 'state' )
    def _erpok(self):
        for o in self:
            r = -1
            if o.state == 'd' and o.item_:
                sql = "select sum( okinqty ) as OKI, sum( okoutqty ) as OKO from simrp_stock where item_=" + str( o.item_.id )
                self.env.cr.execute(sql)
                data = self.env.cr.fetchone()
                if data[ 0 ] is not None:
                    r = data[ 0 ] - data[ 1 ]
            o.erpok = r

    @api.multi
    @api.depends( 'item_', 'state' )
    def _erprej(self):
        for o in self:
            r = -1
            if o.state == 'd' and o.item_:
                sql = "select sum( rejinqty ) as REJI, sum( rejoutqty ) as REJO from simrp_stock where item_=" + str( o.item_.id )
                self.env.cr.execute(sql)
                data = self.env.cr.fetchone()
                if data[ 0 ] is not None:
                    r = data[ 0 ] - data[ 1 ]
            o.erprej = r

    @api.multi
    def approve(self):
        self.name = self.env['ir.sequence'].next_by_code('simrp.physicalstock')
        self.okadj = self.okqty - self.erpok
        self.rejadj = self.rejqty - self.erprej
        self.state = 'a'
        
        self.stock_ = self.env[ 'simrp.stock' ].create( {
                'ref': '%s,%s' % ( 'simrp.physicalstock', self.id ),
                'item_': self.item_.id,
                'okinqty': self.okadj if self.okadj > 0 else 0,
                'rejinqty': self.rejadj if self.rejadj > 0 else 0,
                'okoutqty': -self.okadj if self.okadj < 0 else 0,
                'rejoutqty': -self.rejadj if self.rejadj < 0 else 0,
        } )
        self.stock_.recdate = self.pdate
        return True
        
        
class Shopio(models.Model):
    _name = 'simrp.shopio'
    _inherits = {'simrp.stock': 'stock_'} 
    stock_ =  fields.Many2one( 'simrp.stock', 'Stock', required=True, ondelete="cascade")

    name = fields.Char( 'Code', size = 20, default='<draft>', readonly = True )
    remarks = fields.Char( 'Remarks', size = 200, default="" )
    employee_ = fields.Many2one( 'simrp.employee', 'Receiver', domain=[('active', '=', True)] )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.shopio')
        o = super(Shopio, self).create(vals)
        o.stock_.initStock( False, 'simrp.shopio', o.id, False )
        return o
        
class Openingstock(models.Model):
    _name = 'simrp.openingstock'
    
    name = fields.Char( 'Code', size = 20, default='<draft>', readonly = True )
    
    item_ = fields.Many2one('simrp.item', 'Item' )
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'a', 'Approve' ),
            ], 'State', readonly = True,default='d' )
    
    okqty = fields.Float( 'Ok Stk', digits=(8,2), default=0 )
    rejqty = fields.Float( 'Rej Stk', digits=(8,2), default=0 )
    rate = fields.Float( 'Rate', digits=(8,2) )
    
    value = fields.Float( 'Value', digits=(8,2), compute='_value' )
    stock_ = fields.Many2one( 'simrp.stock', 'Stock', readonly = True )

    @api.multi
    def _value(self):
        for o in self:
            o.value = o.okqty * o.rate

    @api.multi
    def approve(self):
        self.name = self.env['ir.sequence'].next_by_code('simrp.openingstock')
        self.state = 'a'
        
        self.stock_ = self.env[ 'simrp.stock' ].create( {
                'ref': '%s,%s' % ( 'simrp.openingstock', self.id ),
                'item_': self.item_.id,
                'okinqty': self.okqty,
                'rejinqty': self.rejqty,
                'okoutqty': 0,
                'rejoutqty': 0,
        } )
        self.stock_.recdate = datetime.datetime( 1970, 1, 1 )
        return True

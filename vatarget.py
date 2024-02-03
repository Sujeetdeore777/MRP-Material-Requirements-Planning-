import datetime, time
import calendar
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Vatarget(models.Model):
    _name = 'simrp.vatarget'

    item_ = fields.Many2one( 'simrp.item', 'Part', required = True )
    qty = fields.Float('Monthly Target', digits=(8,4) , required = True)
    m4 = fields.Float( 'M/4 ', digits=(8,2), compute='weektarget' ,store = True)
    m24 = fields.Float( 'M/24 ', digits=(8,2), compute='monthtarget' ,store = True)
    week1 = fields.Float( 'Week 1 ', digits=(8,2), compute='weekrecord1' )
    week2 = fields.Float( 'Week 2 ', digits=(8,2), compute='weekrecord2' )
    week3 = fields.Float( 'Week 3 ', digits=(8,2), compute='weekrecord3' )
    week4 = fields.Float( 'Week 4 ', digits=(8,2), compute='weekrecord4' )
    week5 = fields.Float( 'Week 5 ', digits=(8,2), compute='weekrecord5' )
    orders = fields.Float( 'Order ', digits=(8,2), compute='order' )
    total = fields.Float( 'Total ', digits=(8,2), compute='_total' )
    balance = fields.Float( 'Balance ', digits=(8,2), compute='_bal' )

    @api.multi
    @api.depends('qty') 
    def weektarget(self):
        for o in self:
            o.m4 = o.qty / 4

    @api.multi
    @api.depends('qty')
    def monthtarget(self):
        #daily target
        for o in self:
            o.m24 = o.qty / 24
    
    @api.multi
    def order(self):
        for o in self:
            opensaleorder = self.env['simrp.saleorder'].search( [ ('item_', '=', o.item_.id), ( 'state','=','o' ) ] )
            sum = 0
            for i in opensaleorder:
                sum = sum + i.balanceqty
            o.orders = sum
    
    @api.multi
    def weekrecord1(self):
        for o in self:
            date = datetime.date.today()
            start_date = datetime.datetime(date.year, date.month, 1)
            week_1 = datetime.datetime(date.year, date.month, 7)
            end_date = datetime.datetime(date.year, date.month, calendar.mdays[date.month])
            weekrecord = self.env['simrp.dispatch'].search( [ ('invdate', '>=',start_date), ('invdate', '<=',week_1 ), ('item_', '=', o.item_.id), ( 'state','=','i' ) ] )
            sum = 0
            for i in weekrecord:
                sum = sum + i.okoutqty
            o.week1 = sum
    
    @api.multi
    def weekrecord2(self):
        for o in self:
            date = datetime.date.today()
            start_date = datetime.datetime(date.year, date.month, 7)
            end_date = datetime.datetime(date.year, date.month, 14)
            weekrecord = self.env['simrp.dispatch'].search( [ ('invdate', '>=',start_date), ('invdate', '<=',end_date ), ('item_', '=', o.item_.id), ( 'state','=','i' ) ] )
            sum = 0
            for i in weekrecord:
                sum = sum + i.okoutqty
            o.week2 = sum
    
    @api.multi
    def weekrecord3(self):
        for o in self:
            date = datetime.date.today()
            start_date = datetime.datetime(date.year, date.month, 14)
            end_date = datetime.datetime(date.year, date.month, 21)
            weekrecord = self.env['simrp.dispatch'].search( [ ('invdate', '>=',start_date), ('invdate', '<=',end_date ), ('item_', '=', o.item_.id), ( 'state','=','i' ) ] )
            sum = 0
            for i in weekrecord:
                sum = sum + i.okoutqty
            o.week3 = sum
    
    @api.multi
    def weekrecord4(self):
        for o in self:
            date = datetime.date.today()
            start_date = datetime.datetime(date.year, date.month, 21)
            end_date = datetime.datetime(date.year, date.month, 28)
            weekrecord = self.env['simrp.dispatch'].search( [ ('invdate', '>=',start_date), ('invdate', '<=',end_date ), ('item_', '=', o.item_.id), ( 'state','=','i' ) ] )
            sum = 0
            for i in weekrecord:
                sum = sum + i.okoutqty
            o.week4 = sum
    
    @api.multi
    def weekrecord5(self):
        for o in self:
            date = datetime.date.today()
            start_date = datetime.datetime(date.year, date.month, 28)
            end_date = datetime.datetime(date.year, date.month, calendar.mdays[date.month])
            weekrecord = self.env['simrp.dispatch'].search( [ ('invdate', '>=',start_date), ('invdate', '<=',end_date ), ('item_', '=', o.item_.id), ( 'state','=','i' ) ] )
            sum = 0
            for i in weekrecord:
                sum = sum + i.okoutqty
            o.week5 = sum

    @api.multi
    @api.depends('week1','week2','week3','week4','week5') 
    def _total(self):
        for o in self:
            o.total = o.week1 + o.week2 + o.week3 + o.week4 + o.week5

    @api.multi
    @api.depends('qty','total') 
    def _bal(self):
        for o in self:
            o.balance = o.qty - o.total

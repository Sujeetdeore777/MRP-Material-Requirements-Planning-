# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, exceptions
from dateutil.relativedelta import relativedelta
from . import shiftinfo
from num2words import num2words
from urllib.parse import quote
import base64
import json
from odoo.tools import date_utils
import re

import pytz

# from OpenSSL.crypto import load_pkcs12
# from endesive import pdf

#endesive 1.4.5
#wkhtmltopdf 0.12.6

import logging
_logger = logging.getLogger(__name__)
    
class Itemrate(models.Model):
    _name = 'simrp.itemrate'
    
    name = fields.Char( 'Rate Code', size = 50, readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Customer', required = True )
    shipparty_ = fields.Many2one( 'simrp.party', 'Ship to' )
    item_ = fields.Many2one( 'simrp.item', 'Item', domain=[('state', '=', 'a'),('type','in',['fg','scrap','service'])], required = True )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme', required = True ) 
    rate = fields.Float( 'Rate', digits=(8,2), required = True )
    since = fields.Date( 'Since', default=lambda self: fields.Date.today() )
    transport = fields.Selection( [
            ( 'lfob', 'Free delivery to your transporter in Nashik' ),
            ( 'cif', 'Free delivery to your works' ),
            ( 'pay', 'Chargeable' ),
            ( 'pick', 'Pickup arranged by you' ),            
            ( 'o', 'Subcon Process: Only One way delivery paid by us' ),
            ( 'r', 'Subcon Process: Only One way return paid by us' ),
            ( 'b', 'Subcon Process: Delivery and return paid by us' ),
            ( 'f', 'Subcon Process: Delivery and return paid by you' ),            
            ], 'Transport', default='lfob' )
    log = fields.Text( 'Log', readonly = True )
    hsnsac = fields.Char( 'Hsnsac', related='item_.hsnsac' )
    cname = fields.Char( 'Customer Part Name', size = 100 )
    
    customerpo = fields.Char( 'Customer open PO', size = 100 )
    customerpodate = fields.Date( 'Customer PO date', default=lambda self: fields.Date.today() )
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process' )
    inputitem_ = fields.Many2one('simrp.item', 'Input item' )
    byproductitem_ = fields.Many2one('simrp.item', 'Byproduct' )
    moq = fields.Integer('MOQ')

    group = fields.Selection( [
            ( 's', 'S' ),
            ( 'v', 'V' ),
            ], 'Group', default='s' )

    inputuom_ = fields.Many2one( 'simrp.uom', 'Input UOM', related='inputitem_.uom_' )
    outputuom_ = fields.Many2one( 'simrp.uom', 'Output UOM', related='item_.uom_' )
    byproductuom_ = fields.Many2one( 'simrp.uom', 'By-product UOM', related='byproductitem_.uom_' )

    opconv = fields.Float('Output per 1 unit input', digits=(8,5), default=1, required=True)
    byconv = fields.Float('By-product per 1 unit input', digits=(8,5) )
    scrappolicy = fields.Selection([
        ('r', 'Returnable'),
        ('nr', 'Non-Returnable'),
        ], 'Scrap Policy', default='nr', required=True)
    
    active = fields.Boolean(default=True, readonly=True)

    def archive(self):
        for o in self:
            o.active = False
        return True

    def reactivate(self):
        for o in self:
            o.active = True
        return True
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.itemrate')
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Create:', {} )
        return o

    def write(self, vals):
        if 'log' not in vals:
            self.env[ 'simrp.auditlog' ].log( self, 'Change:', vals )
        return super().write(vals)
        
    @api.multi
    def name_get(self):
        result = []
        for o in self.sudo():
            # name = '[' + o.name + ' - ' + o.party_.name + '] ' + o.item_.name
            name = '[' + o.name + '] ' + o.item_.name
            result.append( ( o.id, name ) )
        return result
        
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' ')[-1]
            args = [('name', operator, name)] + args
            args = ['|',('party_.name', operator, name)] + args
            args = ['|',('item_.name', operator, name)] + args
        ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()
    
class Saleorder(models.Model):
    _name = 'simrp.saleorder'
    
    name = fields.Char( 'SO Number', size = 50, readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Customer', required = True )
    pono = fields.Char( 'PO No.', size = 20 )
    podate = fields.Date( 'PO Date', default=lambda self: fields.Date.today() )
    itemrate_ = fields.Many2one( 'simrp.itemrate', 'Item Agreement', required = True )
    item_ = fields.Many2one( 'simrp.item', 'Item', related='itemrate_.item_', readonly = True )
    rate = fields.Float( 'Rate', digits=(8,4), readonly = True )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme', readonly = True ) 
    poqty = fields.Integer( 'PO Qty', required = True )
    commitdate = fields.Date( 'Commit Date' )
    ordervalue = fields.Integer( 'Order Value', compute='_xordervalue', store=True )
    state = fields.Selection( [
            ( 'o', 'Open' ),
            ( 'c', 'Closed' ),
            ], 'State', readonly = True, default='o' )
    balanceordervalue = fields.Integer( 'Bal. Value', readonly = True, compute='_xbalanceordervalue', store=True )
    dispatchqty = fields.Integer( 'Dispatch Qty', readonly = True, compute='_xdispatchqty', store=True )
    complainqty = fields.Integer( 'Complain Qty', readonly = True, compute='_complainqty', store=True )
    balanceqty = fields.Integer( 'Bal. Qty', readonly = True, compute='_xbalanceqty', store=True )
    dispatch_s = fields.One2many( 'simrp.dispatch', 'saleorder_', 'Dispatches' )
    complaint_s = fields.One2many( 'simrp.complaint', 'saleorder_', 'Complaints' )

    wo_s = fields.One2many( 'simrp.wo', 'saleorder_', 'Work orders', readonly = True )
    woqty = fields.Integer( 'WO Qty', compute='_woqty' )
    
    _order = 'id desc'
    
    @api.onchange('itemrate_')
    def change_itemrate_(self):
        self.rate = self.itemrate_.rate
        self.taxscheme_ = self.itemrate_.taxscheme_.id
        if self.itemrate_.customerpo:
            self.pono = self.itemrate_.customerpo
            self.podate = self.itemrate_.customerpodate
    
    def _woqty( self ):
        for o in self:
            q = 0
            for w in o.wo_s:
                q = q + w.tqty
            o.woqty = q
            
    @api.multi
    @api.depends('poqty','dispatchqty','complainqty')
    def _xbalanceqty(self):
        for o in self:
            o.balanceqty = o.poqty - o.dispatchqty + o.complainqty
            if o.balanceqty < 0:
                o.balanceqty = 0
                
    @api.multi
    @api.depends('balanceqty','rate')
    def _xbalanceordervalue(self):
        for o in self:
            o.balanceordervalue = o.balanceqty * o.rate
                
    @api.multi
    @api.depends('dispatch_s','dispatch_s.state','dispatch_s.okoutqty')
    def _xdispatchqty(self):
        for o in self:
            dq = 0
            for d in o.dispatch_s:
                if d.state != 'd':
                    dq = dq + d.okoutqty
            o.dispatchqty = dq

    @api.multi
    @api.depends('complaint_s','complaint_s.qty')
    def _complainqty(self):
        for o in self:
            cq = 0
            for c in o.complaint_s:
                cq = cq + c.qty
            o.complainqty = cq
    
    @api.multi
    @api.depends( 'poqty', 'rate' )
    def _xordervalue(self):
        for o in self:
            o.ordervalue = o.poqty * o.rate
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.saleorder')
        o = super().create(vals)
        o.sudo().rate = o.itemrate_.rate
        o.sudo().taxscheme_ = o.itemrate_.taxscheme_.id
        self.env[ 'simrp.auditlog' ].log( o, 'Create SO:', o.read( [ 'party_', 'itemrate_', 'poqty' ] )[0], False, False )
        return o

    # def write(self, vals):
        # self.env[ 'simrp.auditlog' ].log( self, 'Change:', vals, False )
        # return super().write(vals)

    @api.multi
    def refreshItemRate(self):
        self.rate = self.itemrate_.rate
        self.taxscheme_ = self.itemrate_.taxscheme_.id
        return True

    
    def close(self):
        for o in self:
            o.state = 'c'
        return True
        
    @api.multi
    def open(self):
        self.state = 'o'
        return True
        
    def sostatus(self):
        _logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"+str(self))
        dic={}
        soo = self.search([('state','=','o')])
        for s in soo:
            # _logger.info(s)
            cust = "-"
            if s.party_.shortname:
                cust = s.party_.shortname
            
            dic[s.id] = {'Sono':s.name,'Cust':cust,'Pono': s.pono, 'podate':s.podate,'commitdate':s.commitdate, 'createdon': s.create_date, 'Item':s.item_.name, 'pqty':s.poqty, 'Wqty':s.woqty, 'Bqty':s.balanceqty, 'Bvalue':s.balanceordervalue }
            _logger.info(str(s.party_.name) ) 
            _logger.info(str(s.party_.shortname) ) 
        sorted_list = sorted(dic.items(), key=lambda x: x[1]['Cust'])
        _logger.info(sorted_list)
        return json.dumps(sorted_list,default=date_utils.json_default)
    
    def sostatusTree(self):
        solist = [];
        soo = self.search([('state','=','o')])
        party = self.env['simrp.party'].search([('associate','=','cust')])
        for p in party:
            custlist = [p.name]
            dic = {}
            dic= { 'Cust': custlist, 'Sono':'','Pono':'', 'podate':'','commitdate':'', 'createdon': '', 'Item':'', 'pqty':'', 'Wqty':'', 'Bqty':'', 'Bvalue':'' }
            solist.append(dic)
            for s in soo:
                if s.party_.name == p.name:
                    cust = "-"
                    if s.party_.shortname:
                        cust = s.party_.shortname
                    custlist.append(cust)
                    dic= { 'Cust': custlist, 'Sono':s.name,'Pono': s.pono, 'podate':s.podate,'commitdate':s.commitdate, 'createdon': s.create_date, 'Item':s.item_.name, 'pqty':s.poqty, 'Wqty':s.woqty, 'Bqty':s.balanceqty, 'Bvalue':s.balanceordervalue }
                    solist.append(dic)
        # sorted_list = sorted(dic.items(), key=lambda x: x[1]['Cust'])
        # _logger.info(solist)
        # json.dumps(sorted_list,default=date_utils.json_default)
        return json.dumps(solist,default=date_utils.json_default)
        
        

class Dispatch(models.Model):
    _name = 'simrp.dispatch'
    _inherits = {'simrp.stock': 'stock_'} 
    stock_ =  fields.Many2one( 'simrp.stock', 'Stock', required=True, ondelete="cascade")

    #fields to be removed after transition
    accline_s = fields.One2many( 'simrp.accline', 'dispatch_', 'Accline' )
    shippingcharge = fields.Float( 'Shipping Charges', digits=(8,2), default=0 )
    printed = fields.Boolean( 'Printed', readonly=True )
    dcno = fields.Char( 'DC. No.', readonly=True )
    invno = fields.Char( 'Inv. No.', readonly=True )
    duedate = fields.Date( 'Due Date', readonly = True )
    filename1 = fields.Char( 'FNM', compute='_signinv' )
    file1 = fields.Binary( 'FL1', compute='_signinv' )
    tcopies = fields.Integer()
    counthelp = fields.Integer( ' ', default=1, readonly = True )
    invamt = fields.Float( 'Inv. Amt', digits=(8,2), readonly = True )
    
    name = fields.Char( 'DC No', size = 50, readonly = True )
    invdate = fields.Date( 'DC Date', readonly = True )
    #dcdate = fields.Date( 'DC Date', readonly = True, default=datetime.date.today() )
    #item_ = fields.Many2one( 'simrp.item', 'Item', related='saleorder_.itemrate_.item_', readonly = True )
    #party_ = fields.Many2one( 'simrp.party', 'Party', related='saleorder_.party_', readonly = True )
    #dqty = fields.Integer( 'DC Qty', required = True )
    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Sale Order', readonly = True )
    pono = fields.Char( related='saleorder_.pono' )
    
    group = fields.Selection( related='saleorder_.itemrate_.group' )
    shipparty_ = fields.Many2one( 'simrp.party', related='saleorder_.itemrate_.shipparty_' )
    rate = fields.Float( 'Rate', digits=(8,2), readonly = True )
    amount = fields.Float( 'Amount', digits=(8,2), compute='_amt' )

    pack = fields.Text( 'Packing Details' )
    transport = fields.Text( 'Transport Info' )
    eway = fields.Char( 'E-waybill No' )
    asn = fields.Char( 'Customer ASN' )    
    transportparty_ = fields.Many2one( 'simrp.party', 'Eway Transporter' )
    vehicle = fields.Char( 'EWay Vehicle No', size = 20 )
    distance = fields.Integer( 'Eway Distance' )
    
    #transport_charges = fields.Float( 'Transport Charges' )
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 's', 'Sent' ),
            ( 'i', 'Invoiced' ),
            ( 'c', 'Cancelled' ),
            ], 'State', readonly = True, default='d' )
    
    invoice_ = fields.Many2one( 'simrp.invoice', 'Linked Invoice', readonly = True )
    
    # signurl = fields.Char( 'Digital Sign:', compute='_signurl' )
    
    filename = fields.Char( 'Eway File Name', compute='_filename' )
    ewayfile = fields.Binary( 'Ewayfile', compute='_ewayfile' )

    _order = 'invdate, id'
    
    def _amt( self ):
        for o in self:
            o.amount = o.okoutqty * o.rate
    
    @api.depends('invno','invdate')
    def _filename(self):
        for o in self:
            o.filename = 'EWF_' + o.name + '_' + o.invdate.strftime('%d%m%Y') + '.json'

    @api.depends('invno','invdate')
    def _ewayfile(self):
        for o in self:
            o.ewayfile = self.env[ 'simrp.eway' ].ewayfile( o, o.name, o.distance, o.invamt )
            
    # @api.multi
    # @api.depends('invno','invdate')
    # def _signurl(self):
        # p = self.env["ir.config_parameter"].sudo()
        # for o in self:
            # i = o.party_.vcode + "_" + o.name + "_" + o.invdate.strftime('%d%m%Y')
            # o.signurl = "http://localhost:" + str( p.get_param( "inv.dport" ) ) + "/sign.php?fn=" + quote( i ) + "&w=" + str( p.get_param( "inv.dw" ) ) + "&h=" + str( p.get_param( "inv.dh" ) ) + "&x=" + str( p.get_param( "inv.dx") ) + "&y=" + str( p.get_param( "inv.dy" ) ) + "&sh=" + p.get_param( "inv.dsha1" )


    logfields = [ 'name', 'party_', 'item_', 'rate', 'okoutqty', 'group' ]
    
    @api.model
    def sendwithoutinvoice( self ):
        self.state = 's'
        self.invdate = fields.Date.today()
        self.rate = self.saleorder_.rate
        self.name = self.env['ir.sequence'].next_by_code('simrp.dispatch')
        self.stock_.initStock( self.saleorder_.itemrate_.item_, 'simrp.dispatch', self.id, self.saleorder_.party_ )
        # self.name = self.dcno
        self.recdate = fields.Datetime.now()

    def refreshItemRate( self ):
        if self.state == 'i':
            raise exceptions.UserError('This dispatch is already invoiced. Invoice needs to be cancelled first to proceed.')
        self.rate = self.saleorder_.rate
        self.env[ 'simrp.auditlog' ].log( self, 'REFRESH Dispatch Rate:', self.read( self.logfields )[0], False, False )

    # @api.model
    # def create( self, vals ):
        # o = super().create(vals)
        # return o

    def cancel( self ):
        if self.state == 'i':
            raise exceptions.UserError('This dispatch is already invoiced. Invoice needs to be cancelled first to proceed.')        
        self.okoutqty = 0
        # self.invamt = 0
        self.state = 'c'
        self.invoice = False
        self.env[ 'simrp.auditlog' ].log( self, 'CANCEL DC:', self.read( self.logfields )[0], False, False )
        return True

    def printdc(self):
        self.printed = True
        return self.env.ref('simrp.action_report_printdc').report_action(self)
    def printdcpdf(self):
        self.printed = True
        return self.env.ref('simrp.action_report_printdcpdf').report_action(self)





class Invoice(models.Model):
    _name = 'simrp.invoice'

    #modification methods
    #   customer doesn't take delivery - cancel invoice             remove accentry
    #                                                               remove dispatch linkage
    #                                                               mark cancelled
    #   some item to be removed, some to be added                           remove accentry
    #       if no eway bill created, no issue with GST dept                 remove dispatch linkage
    #       if eway bill created, how is GST law affected?                  move to draft
    #                                                                       while accepting, use same inv no and date
    #   item rate changes                                               same as item change
    #       same eway considerations                                    rate to be updated in DC
    #   shipping charges changed                                    remove accentry
    #       eway?                                                   move to draft, while accepting, use same inv no and date
    #   use cancelled invoice for another customer                          move to draft
    #       eway?                                                           while accepting, use same inv no and date
    
    
    dispatch_s = fields.One2many( 'simrp.dispatch', 'invoice_', 'Dispatches', order="invdate, id")
    # sr., dcno, dcdate, item, hsn, qty, rate, ewaybill, asn, transport, eway transporter, ewayvehicle, eway distance
    accline_s = fields.One2many( 'simrp.accline', 'invoice_', 'Accline', readonly = True )
    
    name = fields.Char( 'Invoice No', size = 50, readonly = True, default='<draft>' )
    invdate = fields.Date( 'Invdate', default=lambda self: fields.Date.today(), readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )

    #pick from 1st dispatch record
    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Sale Order', readonly = True )  
    pono = fields.Char( related='saleorder_.pono', store=True )
    podate = fields.Date( related='saleorder_.podate', store=True )
    shipparty_ = fields.Many2one( 'simrp.party', related='saleorder_.itemrate_.shipparty_' )
    group = fields.Selection( related='saleorder_.itemrate_.group' )
    
    #for single item invoice
    pack = fields.Text( 'Packing Details' )
    transport = fields.Text( 'Transport Info' )
    eway = fields.Char( 'E-waybill No' )
    asn = fields.Char( 'Customer ASN' )
    transportparty_ = fields.Many2one( 'simrp.party', 'Eway Transporter' )
    vehicle = fields.Char( 'EWay Vehicle No', size = 20 )
    distance = fields.Integer( 'Eway Distance' )
    filename = fields.Char( 'Eway File Name', readonly = True )
    ewayfile = fields.Binary( 'Ewayfile', readonly = True )
    
    state = fields.Selection( [
            ( 'd', 'Draft' ),
            ( 'i', 'Invoiced' ),
            ( 'c', 'Cancelled' ),
            ], 'State', readonly = True, default='d' )
    
    # dcno = fields.Char( 'DC. No.', readonly=True )
    # invno = fields.Char( 'Inv. No.', readonly=True )
    # invdate = fields.Date( 'Inv. Date', readonly = True )
    
    tempitem_ = fields.Many2one( 'simrp.item', 'Item', readonly = True )
    tempqty = fields.Float( 'Inv. Qty', digits=(8,2), readonly = True )

    shippingcharge = fields.Float( 'Shipping Charges', digits=(8,2), default=0 )
    #transport_charges = fields.Float( 'Transport Charges' )    
    invamt = fields.Float( 'Inv. Amt', digits=(8,2), readonly = True )
    basicamt = fields.Float( 'Basic Amt', digits=(8,2), readonly = True )
    taxamt = fields.Float( 'Tax Amt', digits=(8,2), readonly = True )
    duedate = fields.Date( 'Due Date', readonly = True )
    # signurl = fields.Char( 'Digital Sign:', compute='_signurl' )
    printed = fields.Boolean( 'Printed', readonly=True )
    tcopies = fields.Integer()   
    invlines = fields.Selection( [
            ( '1', '1' ),
            ( '10', '10' ),
            ( '20', '20' ),
            ], 'Invoice Lines', default='1' )

    filename1 = fields.Char( 'FNM', compute='_signinv' )
    file1 = fields.Binary( 'FL1', compute='_signinv' )

    _order = 'id desc'

    logfields = [ 'name', 'party_', 'group' ]

    # @api.model
    # def create( self, vals ):
        # o = super().create(vals)
        # return o

    def check( o ):
        if len( o.dispatch_s ) == 0:                                            # atleast 1 dc
            raise exceptions.UserError('No Dispatches selected to invoice')
        if len( o.dispatch_s ) > 20:                                            # max 20 dc
            raise exceptions.UserError('Maximum 20 Dispatch items allowed in 1 invoice')
        custpo = o.dispatch_s[ 0 ].saleorder_.pono
        partyid = o.dispatch_s[ 0 ].saleorder_.party_.id
        taxid = o.dispatch_s[ 0 ].saleorder_.taxscheme_.id
        asn = False
        eway = False
        for dc in o.dispatch_s:
            if dc.state == 'c':
                raise exceptions.UserError( 'DC No. ' + dc.name + ' is cancelled' )
            if dc.state == 'i':                                                 # check that dispatches are not invoiced
                raise exceptions.UserError( 'DC No. ' + dc.name + ' is already invoiced' )
            if dc.saleorder_.pono != custpo:                                    # same PO (multiple SO is ok)
                raise exceptions.UserError( 'All DCs should have the same Customer PO' )
            if dc.saleorder_.party_.id != partyid:                               # all dispatch of same customer
                raise exceptions.UserError( 'All DCs should be to the same customer' )
            if dc.saleorder_.taxscheme_.id != taxid:                               # all dispatch of same taxscheme
                raise exceptions.UserError( 'All DCs should be of the same Tax Scheme' )

            # if dc.eway:                                         # if any of dispatch has eway, then invoice eway not allowed
                # eway = True
            # if dc.asn:                                          # if any dispatch has ASN, then invoice should not have asn
                # asn = True
            # if not dc.item_.hsnsac:
                # raise exceptions.UserError('Item HSN/SAC Information missing for item: ' + dc.item_.name )
        # if eway and o.eway:
            # raise exceptions.UserError( 'DC already has an EWay bill, Invoice level Eway bill not required' )
        # if asn and o.asn:
            # raise exceptions.UserError( 'DC already has an ASN, Invoice level ASN not required' )

    def invoice( self ):
        s = self.sudo()
        s.check()

        s.state = 'i'        
        s.saleorder_ = s.dispatch_s[ 0 ].saleorder_.id
        dd = self.party_.creditperiod
        s.duedate = self.invdate + relativedelta(days=+dd)
        
        if s.name == '<draft>':
            s.name = self.env['ir.sequence'].next_by_code('simrp.dispatchinvoice')
            s.invdate = fields.Date.today()

        basicamount = 0
        q = 0
        # eway = 0
        for dc in s.dispatch_s:
            basicamount = basicamount + ( dc.rate * dc.okoutqty )
            q = q + dc.okoutqty
            # if dc.eway:
                # eway = eway + 1
            dc.state = 'i'
        basicamount = basicamount + self.shippingcharge    
        
        s.tempqty = q
        if len( s.dispatch_s ) == 1:
            s.tempitem_ = s.dispatch_s[ 0 ].item_.id
            if not s.pack:
                s.pack = s.dispatch_s[ 0 ].pack
            if not s.transport:
                s.transport = s.dispatch_s[ 0 ].transport
            if not s.eway:
                s.eway = s.dispatch_s[ 0 ].eway
            if not s.asn:
                s.asn = s.dispatch_s[ 0 ].asn
            if not s.transportparty_:
                s.transportparty_ = s.dispatch_s[ 0 ].transportparty_.id
            if not s.vehicle:
                s.vehicle = s.dispatch_s[ 0 ].vehicle
            if not s.distance:
                s.distance = s.dispatch_s[ 0 ].distance
            if not s.filename:
                s.filename = s.dispatch_s[ 0 ].filename
            # if not s.ewayfile:
                # if s.dispatch_s[ 0 ].eway:
                    # s.ewayfile = s.dispatch_s[ 0 ].ewayfile

        s.invamt = self.env[ 'simrp.accentry' ].browse( 1 ).initSale( 
                            self.id, self.party_.account_, 
                            basicamount, self.saleorder_.taxscheme_ )
            
        if not s.eway:
            s.filename = 'EWF_' + s.name + '_' + s.invdate.strftime('%d%m%Y') + '.json'
            s.ewayfile = self.env[ 'simrp.eway' ].ewayfile( s.dispatch_s[ 0 ], s.name, s.distance, s.invamt )
            
                            
        s.basicamt = basicamount
        invline = '1'
        if len( s.dispatch_s ) > 1:
            invline = '10'
        if len( s.dispatch_s ) > 10:
            invline = '20'
        s.invlines = invline
            
        s.taxamt = s.invamt - basicamount
        self.env[ 'simrp.auditlog' ].log( self, 'Invoice:', s.read( self.logfields )[0], False, False )

    def cancel( self ):
        self.cancelLogic( 0 )       #DClogic = 0
    def reverse( self ):
        self.cancelLogic( 1 )       #DClogic = 1
    def draft( self ):
        self.state = 'd'
        
    def cancelLogic( self, DClogic=0 ):
        #   DClogic = 0,    Only cancel invoice
        #           = 1,    Cancel invoice and dispatch both
        for al in self.accline_s:
            al.unlink()

        for dc in self.dispatch_s:
            dc.state = 's'
            if DClogic == 1:
                dc.cancel()
                dc.invoice_ = False
            
        self.saleorder_ = False
    
        tempitem_ = False
        tempqty = False
        # shippingcharge = False

        self.invamt = 0
        self.state = 'c'
        self.env[ 'simrp.auditlog' ].log( self, 'CANCEL Invoice:', self.read( self.logfields )[0], False, False )
        return True

    def use( self ):
        self.state = 'd'
        self.env[ 'simrp.auditlog' ].log( self, 'REDRAFT Invoice:', self.read( self.logfields )[0], False, False )

    def tdebitshortcut( self ):
        # if not self.env['res.users'].has_group('simrp.group_simrp_ceo'):
            # raise exceptions.UserError('You do not have permission to use this action')
        for o in self:
            if len( o.dispatch_s ) == 1:
                td = self.env[ 'simrp.tdebit' ].create( {                
                    'invoice_': o.id,
                    'dispatch_': o.dispatch_s[ 0 ].id,
                    'des': '',
                    'autodesc': True,
                    'basicamount': 0,
                    } )
                td.dcheck()
                td.descalc()
                td.generate()


    @api.model
    def a2w( self ):
        return num2words( self.invamt )
        

    @api.multi
    def printinv(self):
        self.printed = True
        return self.env.ref('simrp.action_report_printinv').report_action(self)

    def _signinv( self ):
        for o in self:
            o.tcopies = 2
            o.filename1 = o.party_.vcode + '_' + o.name + '_' + o.invdate.strftime('%d%m%Y') + '.pdf'
            p = self.env.ref('simrp.action_report_printinvpdf').render_qweb_pdf(res_ids=self.id)[0]
            
            _logger.info( p[0:1000] )
            
            bdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S+00'00'")
            dct = {
                b'sigflags': 3,
                b'sigpage': 1,
                b'sigbutton': True,
                b'contact': b'ks12mobile@gmail.com',
                b'location': b'India',
                b'signingdate': bdate.encode( 'utf-8' ),
                b'reason': b'Invoice Signature',
                b'signature': b'Kaushal Shah',
                b'signaturebox': (475, 75, 600, 100),
            }
                
            signfile = self.env['ir.config_parameter'].sudo().get_param('signfilewithpath')
            signpass = self.env['ir.config_parameter'].sudo().get_param('signfilepassword')
            p12 = load_pkcs12(open(signfile, 'rb').read(), signpass)
            
            ps = pdf.cms.sign( p, dct, p12.get_privatekey().to_cryptography_key(), p12.get_certificate().to_cryptography(), [], 'sha256' )
            
            o.file1 = base64.b64encode( p + ps )

    def signedpdf(self):
        self.printed = True        
        return {
            'name': 'FEC',
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=simrp.invoice&id={}&field=file1&filename_field=filename1&download=true'.format(
                self.id
            ),
            'target': 'new',
        }
            
    @api.multi
    def printinvpdf(self):
        self.printed = True
        self.tcopies = self.party_.copies + 1
        
        r = self.env.ref('simrp.action_report_printinvpdf').report_action(self)
        return r

































class Tqtyupdate(models.TransientModel):
    _name = 'simrp.tqtyupdate'
    
    invoice_ = fields.Many2one( 'simrp.invoice', 'Invoice' )
    qty = fields.Float( 'New Qty', digits=(8,2), default=0 )

    def qtyupdate(self):
        #self.dispatch_.sudo().pack = self.pack
        if len( self.invoice_.dispatch_s ) != 1:
            raise exceptions.UserError( "Only single item invoices modification shortcut allowed" )
        
        n = pytz.utc.localize( datetime.datetime.now() ).astimezone( pytz.timezone( self.env.user.tz or str(pytz.utc) ) )
        r = pytz.utc.localize( self.invoice_.create_date ).astimezone( pytz.timezone( self.env.user.tz or str(pytz.utc) ) )
        
        if ( n.day != r.day ) or ( n.hour - r.hour > 12 ):
            if self.env.user.id != 2:
                raise exceptions.UserError( 'Time limit to change qty expired' )
        
        if self.qty <= 0:
            raise exceptions.UserError( 'Check new qty' )

        self.invoice_.sudo().cancel()
        self.invoice_.sudo().dispatch_s[ 0 ].okoutqty = self.qty
        self.invoice_.sudo().invoice()
        
        # s = self.dispatch_.sudo()
        # for al in s.accline_s:
            # al.unlink()
        
        # s.okoutqty = 
        
        # s.invamt = self.env[ 'simrp.accentry' ].browse( 1 ).initSale( 
                            # s.id, s.party_.account_, 
                            # ( s.rate * s.okoutqty ) + s.shippingcharge,
                            # s.saleorder_.taxscheme_ )

        # self.env[ 'simrp.auditlog' ].log( s, 'QTY UPDATE Invoice:', s.read( s.logfields )[0], False, False )

        #raise exceptions.UserError(  'ok' )
        return { 'type': 'ir.actions.act_view_reload' }


# class Tdispatchsend(models.TransientModel):
    # _name = 'simrp.tdispatchsend'
    
    # dispatch_ = fields.Many2one( 'simrp.dispatch', 'Dispatch', readonly = True )
    # pack = fields.Text( 'Packing Details' )
    # transport = fields.Text( 'Transport Details' )

    # transportparty_ = fields.Many2one( 'simrp.party', 'Eway Transporter' )
    # vehicle = fields.Char( 'EWay Vehicle No', size = 20 )
    # distance = fields.Integer( 'Eway Distance' )

    # state = fields.Selection( [
            # ( 'd', 'Draft' ),
            # ( 's', 'Sent' ),
            # ], 'State', readonly = True, related='dispatch_.state' )

    # @api.multi
    # def update(self):
        # self.dispatch_.sudo().pack = self.pack
        # self.dispatch_.sudo().transport = self.transport
        # self.dispatch_.sudo().transportparty_ = self.transportparty_.id
        # self.dispatch_.sudo().vehicle = self.vehicle
        # self.dispatch_.sudo().distance = self.distance
        
        # bt = self._context.get('buttontype')
        # if self.dispatch_.state == 'd':
            # self.dispatch_.sendwithoutinvoice()
        # if bt == 'i':
            # self.dispatch_.invoice()
        
        # return { 'type': 'ir.actions.act_view_reload' }

class Tdispatchupdate(models.TransientModel):
    _name = 'simrp.tdispatchupdate'
    
    dispatch_ = fields.Many2one( 'simrp.dispatch', 'Dispatch', readonly = True )
    pack = fields.Text( 'Packing Details' )
    transport = fields.Text( 'Transport Details' )
    eway = fields.Char( 'E-waybill No' )
    asn = fields.Char( 'Customer ASN' )
    transportparty_ = fields.Many2one( 'simrp.party', 'Eway Transporter' )
    vehicle = fields.Char( 'EWay Vehicle No', size = 20 )
    distance = fields.Integer( 'Eway Distance' )

    @api.multi
    def update(self):
        self.dispatch_.sudo().pack = self.pack
        self.dispatch_.sudo().transport = self.transport
        self.dispatch_.sudo().eway = self.eway
        self.dispatch_.sudo().asn = self.asn
        self.dispatch_.sudo().transportparty_ = self.transportparty_.id
        self.dispatch_.sudo().vehicle = self.vehicle
        self.dispatch_.sudo().distance = self.distance
        return { 'type': 'ir.actions.act_view_reload' }

        
class Complaint(models.Model):
    _name = 'simrp.complaint'
    
    name = fields.Char( 'Customer Complaint Code', size = 20, readonly = True )
    cdate = fields.Date( 'Complaint date', default=lambda self: fields.Date.today(), required = True )
    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Sale Order', readonly = True )
    item_ = fields.Many2one( 'simrp.item', 'Item', related='saleorder_.item_' )
    party_ = fields.Many2one( 'simrp.party', 'Customer', related='saleorder_.party_' )
    
    raisedby = fields.Char( 'Customer Contact', size = 200 )
    info = fields.Char( 'Method of Intimation' )
    defect = fields.Text( 'Defect Description', required = True )
    action = fields.Text( 'Action', default="" )
    qty = fields.Integer( 'Qty rejected', required = True )
    
    credit_ = fields.Many2one( 'simrp.credit', 'Credit', readonly = True )
    
    state = fields.Selection( [
            ( 'n', 'New' ),
            ( 'a', 'Action' ),
            ( 'cn', 'Credit Note Issued' ),
            ( 'c', 'Closed W/o CN' ),
            ], 'State', default='n' )
            
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.complaint')
        return super(Complaint, self).create(vals)
        
    @api.multi
    def submit( self ):
        if self.action == "":
            raise exceptions.UserError('Enter details of action taken')
        self.state = 'a'
        return True
        
    @api.multi
    def close( self ):
        self.state = 'c'
        return True

    @api.multi
    def credit( self ):
        cn = self.env[ 'simrp.credit' ].create( {
            'party_': self.party_.id,
            'item_': self.item_.id,
            'qty': self.qty,
            'rate': self.saleorder_.rate,
            'ar': self.defect,
            'taxscheme_': self.saleorder_.taxscheme_.id,
        } )
        self.credit_ = cn.id
        self.state = 'cn'
        return True
        
class Credit(models.Model):
    _name = 'simrp.credit'
    
    name = fields.Char( 'Credit Note No.', size = 20, readonly = True )
    cndate = fields.Date( 'Credit Note Date', default=lambda self: fields.Date.today() )

    partydocno = fields.Char( 'Party Doc No.', size = 40 )
    
    
    party_ = fields.Many2one( 'simrp.party', 'Party', readonly = True, required = True )
    item_ = fields.Many2one( 'simrp.item', 'Item', readonly = True )
    qty = fields.Integer( 'Qty rejected' )
    rate = fields.Float( 'Rate' )
    ar = fields.Text( 'Rejection Remarks' )
    aamt = fields.Float( 'Additional amount debited', digits=(8,2), default=0 )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme' ) 
    basicamount = fields.Float( 'Basic Amount', digits=(8,2), readonly = True )
    netamount = fields.Float( 'Net Amount', digits=(8,2), readonly = True )
    cndelivery = fields.Char( 'Proof of Material inwards', size = 200, default="" )

    gstreturn = fields.Selection( [
            ( '1', 'GSTR1 Sales Impact' ),
            ( '3', 'GSTR3 Purchase Impact' ),
            ( '0', 'Non GST' ),
            ], 'Gst Return Impact', default='1' )

    state = fields.Selection( [
            ( 'p', 'Pending' ),
            ( 'a', 'Accounted' ),
            ( 'mrpo', 'Awaiting Material Return' ),
            ( 'mr', 'Material Returned' ),
            ( 'mna', 'Closed w/o Material Movement' ),
            ], 'Status', readonly = True, default='p' )

    accline_s = fields.One2many( 'simrp.accline', 'credit_', 'Account Postings' )
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.credit')
        return super(Credit, self).create(vals)

    @api.multi
    def post( self ):
        self.basicamount = ( self.qty * self.rate ) + self.aamt
        if not self.taxscheme_:
            raise exceptions.UserError('Select Tax Scheme')
        self.env[ 'simrp.accentry' ].browse( 1 ).initCN( self.id, self.party_.account_, self.basicamount, self.taxscheme_ )
        
        self.netamount = self.basicamount + self.taxscheme_.compute( self.basicamount )[ 'tax' ]
        
        self.state = 'a'
        return True

    def reset( self ):
        for a in self.accline_s:
            a.unlink()
        self.state = 'p'

    @api.multi
    def mrpo( self ):
        if not self.item_:
            raise exceptions.UserError('Select Item')
        if not self.qty:
            raise exceptions.UserError('Enter Item Qty')
        if not self.taxscheme_:
            raise exceptions.UserError('Select Tax Scheme')
        po = self.env[ 'simrp.porder' ].create( {
            'party_': self.party_.id,
            'item_': self.item_.id,
            'taxscheme_': self.taxscheme_.id,
            'rate': 0,
            'transport': 'pay',
            'poqty': self.qty,
        } )
        po.approve()

        self.state = 'mrpo'
        return True
        
    @api.multi
    def mr( self ):
        if self.cndelivery == "":
            raise exceptions.UserError('Enter Material Return details first')
        self.state = 'mr'
        return True

    @api.multi
    def close( self ):
        self.state = 'mna'
        return True

class Tinvoice(models.TransientModel):
    _name = 'simrp.tinvoice'

    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Saleorder', readonly = True )
    
    itemrate_ = fields.Many2one( 'simrp.itemrate', 'Item Agreement', required = True )
    dqty = fields.Integer( 'DC Qty', required = True )
    pack = fields.Text( 'Packing Details' )
    transport = fields.Text( 'Transport Details' )
    transport_charges = fields.Float( 'Transport Charges' )

    transportparty_ = fields.Many2one( 'simrp.party', 'Eway Transporter' )
    vehicle = fields.Char( 'EWay Vehicle No', size = 20 )
    distance = fields.Integer( 'Eway Distance' )

    item_ = fields.Many2one( 'simrp.item', 'Item', related='itemrate_.item_', readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Party', related='itemrate_.party_', readonly = True )
    rate = fields.Float( 'Current Rate', digits=(8,2), related='itemrate_.rate', readonly = True )

    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme', related='itemrate_.taxscheme_' ) 
    hsnsac = fields.Char( 'Hsnsac', size = 10, related='itemrate_.item_.hsnsac' )
    cname = fields.Char( 'Customer Part Name', size = 100, related='itemrate_.cname' )
    
    customerpo = fields.Char( 'Customer PO no', size = 100, related='itemrate_.customerpo' )
    customerpodate = fields.Date( 'Customer PO date', related='itemrate_.customerpodate' )

    ratecheck = fields.Boolean( 'Rate change?', default=False )
    newrate = fields.Float( 'New Rate?', digits=(8,2) )

    invoicereplace = fields.Boolean( 'Replace Inv?',default=False )
    replacedispatch_ = fields.Many2one( 'simrp.dispatch', 'Replace Doc' )
    
    group = fields.Selection( [
            ( 's', 'S' ),
            ( 'v', 'V' ),
            ], 'Group', default='s' )
    
    dispmode = fields.Selection( related='itemrate_.party_.dispmode' )
    singleinvoice = fields.Boolean( 'Single Item Invoice' )

    @api.onchange('itemrate_', 'dqty')
    def type_change(self):
        if not self.distance:
            self.distance = self.party_.distance

    @api.multi
    def updaterate(self):
        if self.ratecheck:
            if self.newrate <= 0:
                raise exceptions.UserError('Enter correct New Rate, or disable the Rate Change Option')
            if not self.itemrate_.log:
                self.sudo().itemrate_.log = ""
            self.sudo().itemrate_.log = self.itemrate_.log + "\n On " + shiftinfo.getnowlocaltimestring( self ) + ", Old Rate: " + str( self.itemrate_.rate ) + " changed to " + str( self.newrate ) + " by " + self.env.user.name
            self.sudo().itemrate_.rate = self.newrate
            self.sudo().itemrate_.since = fields.Date.today()
            self.ratecheck = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.tinvoice',
            'target': 'new',
            #'res_id': d.id,
            'context': {'default_group':'v', 'default_itemrate_': self.itemrate_.id, 'default_dqty': self.dqty }
            }
    
    # def replaceinvoicefn( self ):
        # # For replacing of cancelled invoices
        # if not self.invoicereplace:
            # raise exceptions.UserError('Select the replace invoice option to use this function')
        # if not self.replacedispatch_:
            # raise exceptions.UserError('Select the replace invoice document to use this function')
        # self.replacedispatch_.party_ = self.itemrate_.party_.id
        # self.replacedispatch_.item_ = self.itemrate_.item_.id,
        # self.replacedispatch_.okoutqty = self.dqty
        # self.replacedispatch_.saleorder_ = self.saleorder_.id,
        # self.replacedispatch_.pack = self.pack
        # self.replacedispatch_.transport = self.transport
        # self.replacedispatch_.shippingcharge = self.transport_charges
        # self.replacedispatch_.transportparty_ = self.transportparty_.id
        # self.replacedispatch_.vehicle = self.vehicle
        # self.replacedispatch_.distance = self.distance
        # self.replacedispatch_.eway = ''
        # self.replacedispatch_.asn = ''
        # self.replacedispatch_.vehicle = ''
        # self.replacedispatch_.printed = False

        # self.replacedispatch_.state = 'i'
        # dd = self.itemrate_.party_.creditperiod
        # self.replacedispatch_.duedate = self.replacedispatch_.invdate + relativedelta(days=+dd)
        # self.replacedispatch_.invamt = self.env[ 'simrp.accentry' ].browse( 1 ).initSale( 
                            # self.replacedispatch_.id, self.itemrate_.party_.account_, 
                            # ( self.replacedispatch_.rate * self.replacedispatch_.okoutqty ) + self.replacedispatch_.shippingcharge,
                            # self.replacedispatch_.saleorder_.taxscheme_ )
        # self.replacedispatch_.env[ 'simrp.auditlog' ].log( self, 'Invoice:', self.replacedispatch_.read( self.replacedispatch_.logfields )[0], False, False )

        # if self.saleorder_.balanceqty <= 0:
            # self.saleorder_.state = 'c'
        
        # return {
            # 'type': 'ir.actions.act_window',
            # 'view_type': 'form',
            # 'view_mode': 'form',
            # 'res_model': 'simrp.dispatch',
            # 'target': 'current',
            # 'res_id': self.replacedispatch_.id,
            # }
        
    

    def update(self):
        if self.dqty <= 0:
            raise exceptions.UserError('Enter correct Dispatch Qty')
        
        if self.saleorder_:
            so = self.saleorder_
        else:
            # v group
            vscmargin = float( self.env['ir.config_parameter'].sudo().get_param('vscmargin') )
            if vscmargin <= 0:
                raise exceptions.UserError( 'VSC Margin not set' )
            round2=lambda x,y=None: round(x + 0.0000000001,y)
            porate = round2( self.itemrate_.rate / vscmargin, 2 )
            party = self.env[ 'simrp.party' ].search( [('name','=','VIREN SALES CORPORATION')] )
            tax = self.env[ 'simrp.taxscheme' ].search( [('name','=','Purchase On CGST+SGST 18%')] )

            po = self.sudo().env[ 'simrp.porder' ].create( {
                'party_': party.id,
                'item_': self.itemrate_.item_.id,
                # 'itemprocess_': self.,
                'taxscheme_': tax.id,
                'rate': porate,
                'poqty': self.dqty, } )

            po.approve()
            grnm = self.sudo().env[ 'simrp.grnmaster' ].create( {
                'dcno': po.name,
                'party_': party.id, } )
            
            tgrn = self.sudo().env[ 'simrp.tgrn' ].create( {
                'grnmaster_': grnm.id,
                'porder_': po.id,
                'qtydc': self.dqty,
                'qtyactual': self.dqty,
                'phycounter': 'Auto VSC GRN',
                'grnmode': 'porder' } )
            grn = tgrn.grn()

            grn.qcinspection_.deleteqci()
            grn.qcstate = 'na'
            
            po.close()
            
            so = self.sudo().env[ 'simrp.saleorder' ].sudo().create( {
                'party_': self.itemrate_.party_.id,
                'pono': self.itemrate_.customerpo,
                'podate': self.itemrate_.customerpodate,
                'itemrate_': self.itemrate_.id,
                'poqty': self.dqty,
                'commitdate': fields.Date.today(),
                'state': 'c',
                } )
                
        if so.balanceqty < self.dqty:
            raise exceptions.UserError('Dispatch Qty is more than SO balance qty')

        if self.itemrate_.item_.okstock < self.dqty:
            raise exceptions.UserError('FG Stock shortage')
            
        d = self.sudo().env[ 'simrp.dispatch' ].create( {
            'item_': self.itemrate_.item_.id,
            'party_': self.itemrate_.party_.id,
            'okoutqty': self.dqty,
            'saleorder_': so.id,
            'pack': self.pack,
            'transport': self.transport,
            # 'shippingcharge': self.transport_charges,
            'transportparty_': self.transportparty_.id,
            'vehicle': self.vehicle,
            'distance': self.distance,
            'invdate': fields.Date.today(),
        } )
        d.sudo().sendwithoutinvoice()
        if so.balanceqty <= 0:
            so.sudo().state = 'c'
        
        resmodel = 'simrp.dispatch'
        resid = d.id
        if ( self.dispmode == 'inv' ) or ( self.singleinvoice ):
            inv = self.sudo().env[ 'simrp.invoice' ].create( {
                'party_':  self.itemrate_.party_.id,
                'saleorder_': so.id,
                'shippingcharge': self.transport_charges,
                } )
                
            d.invoice_ = inv.id
                
            inv.invoice()
            resmodel = 'simrp.invoice'
            resid = inv.id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': resmodel,
            'target': 'current',
            'res_id': resid,
            }
            
class Tdebit(models.TransientModel):
    _name = 'simrp.tdebit'

    group = fields.Selection( [
            ( 's', 'S' ),
            ( 'v', 'V' ),
            ], 'Group', default='s' )

    invoice_ = fields.Many2one( 'simrp.invoice', 'Invoice', required = True )
    invdate = fields.Date( related='invoice_.invdate' )
    
    dispatch_ = fields.Many2one( 'simrp.dispatch', 'Dispatch', required = True )
    party_ = fields.Many2one( related='dispatch_.stock_.party_' )
    item_ = fields.Many2one( related='dispatch_.stock_.item_' )
    okoutqty = fields.Float( related='dispatch_.stock_.okoutqty' )
    saleorder_ = fields.Many2one( related='dispatch_.saleorder_' )
    rate = fields.Float( related='dispatch_.rate' )
    itemrate_ = fields.Many2one( related='dispatch_.saleorder_.itemrate_' )
    taxscheme_ = fields.Many2one( related='dispatch_.saleorder_.itemrate_.taxscheme_' ) 
    
    newrate = fields.Float( 'New Rate', digits=(8,4) )
    autodesc = fields.Boolean( 'Auto description?', default=False )
    refno = fields.Char( 'Customer Ref', default="" )
    des = fields.Text( 'Debit Description', required = True )

    basicamount = fields.Float( 'Basic Amount', digits=(8,2), default=0, required=True )

    @api.onchange('dispatch_')
    def dcheck(self):
        if self.dispatch_:
            self.newrate = self.itemrate_.rate
    @api.onchange('invoice_')
    def dcheck1(self):
        if self.invoice_:
            self.dispatch_ = self.invoice_.dispatch_s[ 0 ]
            self.newrate = self.itemrate_.rate
            
    @api.onchange('newrate', 'refno', 'autodesc')
    def descalc(self):
        self.basicamount = self.okoutqty * ( self.newrate - self.rate )
        if self.autodesc and self.dispatch_:
            grr = ''
            if self.refno:
                grr = self.refno
            pono = ''
            if self.saleorder_.pono:
                pono = self.saleorder_.pono
            self.des = 'Rate amendment against our Invoice No. ' + self.invoice_.name + " dt. " + self.invdate.strftime('%d.%m.%Y') + '\n' + 'Item: ' + self.item_.name + '\nQty: ' + str( self.okoutqty ) + '\n' + 'OLD Inv. Rate: Rs.' + "{:.3f}".format( self.rate ) + ', amended to NEW: Rs.' + "{:.3f}".format( self.newrate ) + '\nYour GR Reference: ' + grr + '\nAgst. your PO No.: ' + pono

            
    def generate(self):
        if self.basicamount <= 0:
            raise exceptions.UserError('Enter correct Basic Amount')
        if not self.des:
            raise exceptions.UserError('Enter Debit Description')
        if not self.dispatch_:
            raise exceptions.UserError('Select Dispatch')
        
        dn = self.env[ 'simrp.debit' ].sudo().create( {
                'party_': self.party_.id,
                'ar': self.des,
                'basicamount': self.basicamount,
                'taxscheme_': self.taxscheme_.id,
                'group': self.group,
            } )

        sdate = self.env['ir.config_parameter'].sudo().get_param('systemdate')
        if sdate:
            dn.rdate = datetime.datetime.strptime( sdate, '%d/%m/%Y' ).date()
        
        dn.sudo().post()
        dn.sudo().close()
        # r = dn.sudo().printDCpdf()
        # r[ 'target' ] = 'self'
        # return r
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.debit',
            'target': 'current',
            'res_id': dn.id,
            }

class Twogen(models.TransientModel):
    _name = 'simrp.twogen'

    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Saleorder', readonly = True )    
    itemrate_ = fields.Many2one( 'simrp.itemrate', 'Item Agreement', readonly = True )
    woqty = fields.Integer( 'WO Qty', required = True )
    
    def genwo(self):
        wo = self.env[ 'simrp.wo' ].create( {
                                    'saleorder_': self.saleorder_.id,
                                    'item_': self.itemrate_.item_.id,
                                    'tqty': self.woqty,
                                    } )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.wo',
            #'target': 'new',
            'res_id': wo.id,
            }

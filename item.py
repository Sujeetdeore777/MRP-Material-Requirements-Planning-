# -*- coding: utf-8 -*-
import difflib
import datetime
from odoo import api, fields, models
from datetime import date
import logging
_logger = logging.getLogger(__name__)

ITEM_TYPE_LIST = [                                          #Misc GRN  PO+GRN ProcessTool Itemrate QA Category  QA Instrument GRN+QC PO-WO WO
        ('rmb', 'Raw Material (RM-Basic)'),                 #              .                                                  .         .
        ('bo', 'Input Parts (Boughtout / WIP)'),            #              .                                                  .         .
        ('fg', 'Finished Goods (FG)'),                      #              .                .                                 .             .
        ('scrap','Scrap FG'),                               #              .                .
        ('equipment','Equipment'),                          #              .       .                    .            .
        ('instrument','Instrument'),                        #              .                            .            .
        ('cons','Consumable (stationery / gloves / etc)'),  #   .          o       .
        ('insert', 'Consumable Tools / inserts / Oils'),    #   .          o1      .
        ('service', 'FG Services')                          #              .                 .
        ]
        
class Itemcategory(models.Model):
    _name = 'simrp.itemcategory'
    _description = 'Item Categories'
    
    name = fields.Char('Category Name', required=True)
    type = fields.Selection( ITEM_TYPE_LIST, 'Category Type', required=True)

class Uom(models.Model):
    _name = 'simrp.uom'
    
    name = fields.Char( 'UOM Name', size = 15, required = True )
    gstcode = fields.Char( 'GST UOM Code EWay', size = 15, required = True, default='' )
    gstr1code = fields.Char( 'GST UOM Code R1', size = 15, default='' )
    #gstr1code1 = fields.Char( 'Dummy delete', size = 15, default='' )


class Item(models.Model):
    _name = 'simrp.item'
    _description = 'Item'

    name = fields.Char(compute='_xname', store=True)
    shortname = fields.Char(compute='_shortname')
    code = fields.Char('Item Code', readonly=True)
    shortcode = fields.Char('Short Name')

    des = fields.Char('Description')
    type = fields.Selection( ITEM_TYPE_LIST, 'Item Type', required=True, default='fg')
    uom_ = fields.Many2one( 'simrp.uom', 'Base UOM', default=1 ) 
    dwg_no = fields.Char('Dwg/ Part/ Sr. No')
    rev = fields.Char('Revision')
    net_wt = fields.Float('Net Weight (kg)')
    category = fields.Many2one('simrp.itemcategory', 'Item Category', required=True, domain="[('type', '=', type)]")
    state = fields.Selection([('d', 'Draft'), ('a', 'Locked')], default='d',readonly=True)
    active = fields.Boolean(default=True, readonly=True)
    costrm = fields.Float( 'Cost RM/Pc', digits=(8,2), compute='_costrm' )
    costout = fields.Float( 'Cost Out Sourcing/Pc', digits=(8,2), compute='_costoutsource' )
    scrapweight = fields.Float( 'Scrap Weight/Pc', digits=(8,2), compute='_scrapweight' )
    valuescrap = fields.Float( 'Value of Scrap/pc', digits=(8,2), compute='_scrapvalue' )

    brand = fields.Char()
    lc = fields.Char()
    range = fields.Char()
    log = fields.Text( 'Log' , readonly = True)
    # transcript = fields.Text( 'Current Transcript' ,readonly=True)
    iofile_s = fields.One2many( 'simrp.iofile', 'item_', 'Item Files' )
    itemprocess_s = fields.One2many('simrp.itemprocess', 'item_', 'Process Sequence (Flow)', domain=['|',('active','=',False),('active','=',True)])
    bom_s = fields.One2many( 'simrp.bom', 'item_', 'BOM', domain=['|',('active','=',False),('active','=',True)] )
    hsnsac = fields.Char('GST HSN/SAC', default='')

    okstock = fields.Float( 'Okstock', digits=(8,2), compute='_okrejstock' )
    rejstock = fields.Float( 'Rejstock', digits=(8,2), compute='_okrejstock' )
    
    fgtemp = fields.Float( 'Fgtemp', digits=(8,2) )
    log = fields.Text( 'Log', readonly = True )
    lasttranscript = fields.Text( 'Lasttranscript', readonly = True )
    useinsales = fields.Boolean('Use sales report', default = True)


    #bi = fields.Binary( 'BFile', attachment=True )
    
# instrument needs calibration, redflags and maintenance
# equipment needs redflags and maintenance
#        'stock_mgmt_method': fields.selection([('auto', 'Auto'), ('manual', 'Manual')], 'Stock Management Method'),  
#        'rol': fields.float('ROL', digits = (6, 2), help='Reorder Level'),
#        'min_level': fields.float('Minimum Level', digits = (6, 2)),
#        'soq': fields.float('SOQ', digits = (6, 2),help='Standard order Qty'),
#        'kanban_lot_qty':fields.integer('Kanban Lot Qty'),
#        'plantdefaultstorelocation_s': fields.one2many('master.plantdefaultstorelocation', 'product_', 'Default Store', delete='cascade'),

    def bookzerofg( self ):
        for o in self:
            o.fgtemp = - o.okstock
            o.bookfg()
            
    def bookfg( self ):
        for o in self:
            q = self.fgtemp
            if q > 0:
                for bi in o.bom_s:
                    #consume bi stock q * bi.bomqty
                    s = self.env[ 'simrp.stock' ].create( { 'okoutqty': q * bi.bomqty, } )
                    s.initStock( bi.bomitem_, 'simrp.item', o.id, False )
                s = self.env[ 'simrp.stock' ].create( { 'okinqty': q } )
                s.initStock( o, 'simrp.item', o.id, False )
            self.fgtemp = -1

    @api.multi
    def prprint(self):
        return self.env.ref('simrp.action_report_prprint').report_action(self)

    @api.multi
    def _costrm(self):
        for o in self:
            c_rm = 0
            for b in o.bom_s:
                bi = b.bomitem_
                if len( bi.bom_s ) == 0:
                    pur_order = self.env['simrp.porder'].search( [ ('item_', '=', bi.id), ( 'state','!=','d' ) ],limit=1, order="podate desc" )
                    rm = 0
                    if pur_order:
                        rm = ( pur_order.rate + pur_order.loadrate + pur_order.testrate ) * b.bomqty
                    c_rm = c_rm + rm
                else:
                    for bom1 in bi.bom_s:
                        c_rm = c_rm + bom1.bomitem_.costrm
            o.costrm = c_rm


    @api.multi
    @api.depends('des', 'type', 'dwg_no', 'rev', 'category', 'code', 'brand', 'lc', 'range')
    def _xname(self):
        for o in self:
            r = ''
            des = ''
            cname = ''
            if o.category:
                cname = o.category.name
            if o.des:
                des = o.des
            if o.type == 'rmb':
                r = cname + ' ' + des
            elif o.type in ['bo', 'cons']:
                r = des
                if o.brand:
                    r = r + ' #' + o.brand 
                r = r +  ' (' + cname + ')'
            elif o.type == 'fg':
                if o.dwg_no:
                    r = o.dwg_no
                if o.rev:
                    r = r + ' rev. ' + o.rev
                r = r + ', ' + des
            elif o.type in ['scrap']:
                r = cname + ' ' + des
            elif o.type in ['equipment']:
                r = des 
                if o.dwg_no:
                    r = r + ' S.No.' + o.dwg_no
                if o.brand:
                    r = r + ' #' + o.brand 
                r = r + ' (' + cname + ')'
            elif o.type in ['instrument']:
                if o.range:
                    r = o.range 
                r = r + ' ' + des + ' ' + cname
                if o.lc:
                    r = r + ' LC-' + o.lc 
            elif o.type in ['insert']:
                r = cname + ' - ' + des
                if o.brand:
                    r = r + ' #' + o.brand 
            elif o.type in ['service']:
                r = des + " (Service)"

            if o.code:
                r = '[' + o.code + '] ' +  r
            o.name = r

    @api.multi
    @api.depends('des', 'dwg_no')
    def _shortname(self):
        for o in self:
            r = ''
            if o.des:
                r = o.des
            if o.dwg_no:
                r = r + ', ' + o.dwg_no
            o.shortname = r[:15]

    @api.onchange('type')
    def type_change(self):
        self.category = False
        self.dwg_no = ''
        self.rev = ''
        self.net_wt = ''
        self.brand = ''
        self.lc = ''
        self.range = ''
        self.uom_ = 1
        if self.type in ['rmb','scrap']:
            self.uom_ = 2
        if self.type in ['service']:
            self.uom_ = 5
        
    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('simrp.item')
        return super().create(vals)
        
    
    def transcribe( self ):
        o = self
        l = "|NAME|" + o.name + "\n|TYPE|" + str(o.type) + "\n"
        for i in self.bom_s:
            l = l + "|IBOM|" + str(i.bomitem_.name) + " |SIZE|" + i.t + " |BQTY|" + str(i.bomqty) + "\n"
        for i in self.itemprocess_s:
            l = l + "|IPRO|" + str(i.name) + "\n"
        return l
        
    def updateTranscript( self ):
        prevtrans = self.lasttranscript
        if not prevtrans:
            prevtrans = ''
        newtran = self.transcribe()
        if prevtrans != newtran:
            diffInstance = difflib.HtmlDiff(wrapcolumn=80).make_table( prevtrans.split('\n'), newtran.split('\n') )
            # print( diffInstance )
            self.env[ 'simrp.auditlog' ].log( self, diffInstance, {}, True, False )        
            self.lasttranscript = newtran
        return
    
    def archive(self):
        for o in self:
            if ( o.okstock != 0 ) or ( o.rejstock != 0 ):
                raise exceptions.UserError('Item stock is not zero')
            o.active = False
            irs = self.env[ 'simrp.itemrate' ].search( [ ('item_','=',o.id) ] )
            for ir in irs:
                irs.archive()
        return True

    def approve(self):
        self.updateTranscript()
        self.state = 'a'
        return True

    def modify(self):
        self.state = 'd'
        return True

    # @api.multi
    # def submit(self):
        # self.state = 's'
        # return True

    @api.multi
    def reactivate(self):
        self.active = True
        return True
        
    @api.multi
    def _costoutsource(self):
        for o in self:
            outsource_sum = 0
            for p in self.itemprocess_s:
                if p.allowsubcon:
                    temp = -1
                    for s in p.subcon:
                        if s.active == True:
                            if temp < s.value:
                                temp = s.value
                    outsource_sum = outsource_sum + temp
            o.costout = outsource_sum

    @api.multi
    def _scrapweight(self):
        for o in self:
            totalscrap = 0
            for p in self.itemprocess_s:
                sum = 0
                for i in p.byproduct:
                    sum = sum + i.qty
                totalscrap = totalscrap + sum
            o.scrapweight = totalscrap

    @api.multi
    def _scrapvalue(self):
        for o in self:
            rate = 0
            dc_value = self.env['simrp.dispatch'].search( [ ('item_', '=', o.id), ( 'state','=','i' ) ], order = "invdate desc", limit= 1 )
            if len(dc_value) > 0:
                rate = dc_value.rate
            sum = 0
            for p in self.itemprocess_s:
                for i in p.byproduct:
                    sum = sum + ( rate * i.qty)
            o.valuescrap = sum

    def _okrejstock( self ):
        for o in self:
            oks = 0
            rejs = 0
            self.env.cr.execute("SELECT sum(okinqty), sum(okoutqty), sum(rejinqty), sum(rejoutqty) FROM simrp_stock WHERE item_ =" + str( o.id ) )
            d = self.env.cr.fetchone()
            if d[ 0 ] is not None:
                oks = d[ 0 ] - d[ 1 ]
                rejs = d[ 2 ] - d[ 3 ]
            o.okstock = oks
            o.rejstock = rejs
            _logger.info( '############################################### ' + o.name )
            _logger.info( d[ 0 ] )
            _logger.info( d[ 1 ] )

# class Upgrade(models.TransientModel):
    # _name = 'simrp.upgrade'
    
    # name = fields.Char( 'Upgrade', size = 50 )

    # @api.model
    # def default_get(self, fields_list):
        # self.env[ 'ir.module.module' ].browse( 255 ).button_immediate_upgrade()
        # return {}

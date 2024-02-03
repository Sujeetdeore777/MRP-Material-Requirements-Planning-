# -*- coding: utf-8 -*-

import odoo.tools as tools
import datetime, time, math
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json
from odoo.tools import date_utils

import logging
_logger = logging.getLogger(__name__)

class Wo(models.Model):
    _name = 'simrp.wo'
    
    name = fields.Char( 'Wo', size = 20, readonly = True )
    wodate = fields.Date( 'Wo date', default=lambda self: fields.Date.today(), readonly = True )
    item_ = fields.Many2one( 'simrp.item', 'Item', domain=[('state', '=', 'a')], required = True )
    tqty = fields.Integer( 'Target qty', required = True )

    type = fields.Selection( [
            ( 'n', 'Normal' ),
            ( 't', 'Tracking (Non Stock)' ),
            ], 'WO Type', required = True, default='n' )
            
    state = fields.Selection( [
            ( 'o', 'Open' ),
            ( 's', 'Submit for Review' ),
            ( 'c', 'Closed' ),
            ], 'State', readonly = True, default='o' )
            
    wobom_s = fields.One2many( 'simrp.wobom', 'wo_', 'WO bom', readonly = True )
    woissue_s = fields.One2many( 'simrp.woissue', 'wo_', 'Wo Material Issue', readonly = True )
    woprocess_s = fields.One2many( 'simrp.woprocess', 'wo_', 'Woprocess', readonly = True )
    wotool_s = fields.One2many( 'simrp.wotool', 'wo_', 'Wotool', readonly = True )
    wobyproduct_s = fields.One2many( 'simrp.wobyproduct', 'wo_', 'Wobyproduct', readonly = True )
    processsubcon_s = fields.One2many( 'simrp.processsubcon', string='Processsubcon', compute="_processsubcon_s" )
    subcondc_s = fields.One2many( 'simrp.subcondc', 'wo_', 'Subcondc', readonly = True )
    woproduction_s = fields.One2many( 'simrp.woproduction', 'wo_', 'Woproduction', readonly = True )
    wotoolconsume_s = fields.One2many( 'simrp.wotoolconsume', 'wo_', 'Wotoolconsume', readonly = True )
    womfg_s = fields.One2many( 'simrp.womfg', 'wo_', 'Womfg', readonly = True )

    wook = fields.Float( 'WO Ok Qty', digits=(8,2), compute='_woqty' )
    worej = fields.Float( 'WO Rej Qty', digits=(8,2), compute='_woqty' )
    
    saleorder_ = fields.Many2one( 'simrp.saleorder', 'Saleorder', readonly = True )
    woprogress = fields.Text( 'Woprogress', compute='_woprogress' )
    woprogresscompact = fields.Text( 'Woprogresscompact', compute='_woprogresscomp' )

    porder_s = fields.One2many( 'simrp.porder', 'wo_', 'Purchase Orders' )
    
    _order = 'id desc'
    s = ''
    
    def _woqty( self ):
        for o in self:
            r = 0
            r1 = 0
            for m in o.womfg_s:
                r = r + m.okqty
                r1 = r1 + m.rejqty
            o.wook = r
            o.worej = r1

    def _woprogress( self ):
        rp = self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        cmd = ""
        with open( rp + '/simrp/woprogress.py', 'r') as file:
            cmd = file.read()
        for o in self:
            exec( cmd )
            # _logger.info( 'SSSSSSSSSSSSSSSSSSSSSSSS ' + self.s );
            o.woprogress = self.s
            
    def _woprogresscomp( self ):
        rp = self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']
        cmd = ""
        with open( rp + '/simrp/woprogresscompact.py', 'r') as file:
            cmd = file.read()
        for o in self:
            exec( cmd )
            # _logger.info( 'SSSSSSSSSSSSSSSSSSSSSSSS ' + self.s );
            o.woprogresscompact = self.s
            
    @api.multi
    @api.depends( 'item_' )
    def _processsubcon_s(self):    
        for o in self:
            slist = self.env[ 'simrp.processsubcon' ].search( [('item_','=',o.item_.id)] )
            o.processsubcon_s = slist

    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.wo')
        o = super().create(vals)
        if not o.item_.bom_s:
            raise exceptions.UserError( 'No BOM defined for FG' )
        if not o.item_.itemprocess_s:
            raise exceptions.UserError( 'No Processes defined for FG' )
        
        for b in o.item_.bom_s:
            if b.active and b.bomqty > 0:
                    self.env[ 'simrp.wobom' ].create({ 'wo_': o.id, 'bomitem_': b.bomitem_.id, 'bomqty': b.bomqty })
        for p in o.item_.itemprocess_s:
            if p.active:
                # wop = self.env[ 'simrp.woprocess' ].create({ 'wo_': o.id, 'woitem_': o.item_.id, 'name': o.name + '-' + str( p.seq ), 'itemprocess_': p.id, 'speed': math.ceil( p.speed ), 'tqtytoprocess': o.tqty, })
                wop = self.env[ 'simrp.woprocess' ].create({ 'wo_': o.id, 'woitem_': o.item_.id, 'name': o.name + '-' + str( p.seq ), 'itemprocess_': p.id, 'speed': round( p.speed, 1 ), 'tqtytoprocess': o.tqty, })
                for t in p.toollist:
                    self.env[ 'simrp.wotool' ].create( { 'wo_': o.id, 'woprocess_': wop.id, 'item_': t.item_.id, 'expectedlife': t.expectedlife } )
                #for b in p.byproduct:
                #    self.env[ 'simrp.wobyproduct' ].create( { 'wo_': o.id, 'woprocess_': wop.id, 'item_': b.item_.id, 'qty': b.qty } )
        self.env[ 'simrp.auditlog' ].log( o, 'Create WO: ', o.read( [ 'name', 'item_', 'tqty', 'saleorder_' ] )[0], False, False )
        return o

    def refresh(self):
        for o in self:
            for b in o.item_.bom_s:
                if b.active and b.bomqty > 0:
                    a = True
                    for wb in o.wobom_s:
                        if b.bomitem_.id == wb.bomitem_.id:
                            a = False
                            wb.bomqty = b.bomqty
                    if a:
                        self.env[ 'simrp.wobom' ].create({ 'wo_': o.id, 'bomitem_': b.bomitem_.id, 'bomqty': b.bomqty })
            
            for p in o.item_.itemprocess_s:
                if p.active == True:
                    a = True
                    for wp in o.woprocess_s:
                        if wp.itemprocess_.id == p.id:
                            a = False
                            wp.speed = math.ceil( p.speed )
                            wp.woitem_ = o.item_.id
                            wp.tqtytoprocess = o.tqty
                    if a:
                        wop = self.env[ 'simrp.woprocess' ].create({ 'wo_': o.id, 'woitem_': o.item_.id, 'name': o.name + '-' + str( p.seq ), 'itemprocess_': p.id, 'speed': p.speed, 'tqtytoprocess': o.tqty, })
                        for t in p.toollist:
                            self.env[ 'simrp.wotool' ].create( { 'wo_': o.id, 'woprocess_': wop.id, 'item_': t.item_.id, 'expectedlife': t.expectedlife } )
            #for b in p.byproduct:
            #    self.env[ 'simrp.wobyproduct' ].create( { 'wo_': o.id, 'woprocess_': wop.id, 'item_': b.item_.id, 'qty': b.qty } )
            # by products should be auto created during ok qty booking of production processes
        return o

    def unlink( self ):
        raise exceptions.UserError( 'WO delete disabled' )
        return super(Wo,self).unlink()

        
    @api.multi
    def submit( self ):
        for o in self.woproduction_s:
            if o.state != 'c':
                raise exceptions.UserError( 'All Production Records are not closed' )
        for o in self.subcondc_s:
            if o.state != 'c':
                raise exceptions.UserError( 'All Subcon DCs are not closed' )
            
        self.state = 's'
        self.env[ 'simrp.auditlog' ].log( self, 'Submit WO: ', self.read( [ 'name', 'item_', 'tqty', 'saleorder_', 'wook', 'worej' ] )[0], False, False )
        return True

    @api.multi
    def close( self ):
        self.state = 'c'
        return True

    @api.multi
    def reopen(self):
        self.state = 'o'
        return True
        
    @api.multi
    def wostatus(self, cname):
        _logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"+str(self))
        dic={}
        woo = self.search([('state','=','o'),'|','|',('item_.name', 'ilike', cname ),('saleorder_.party_.name', 'ilike', cname ),('saleorder_.name', 'ilike', cname )])
        if woo:
            for w in woo:
                # _logger.info(w.woprogresscompact)
                r = '[' + w.item_.code + ']'
                dic[w.id] = { 'Wono' : w.name, 'Woprogresshtml' : w.woprogresscompact , 'customer' : w.saleorder_.party_.shortname,'des':w.item_.des,'partno' : w.item_.dwg_no, 'code':r, 'Woqty':w.tqty ,'linkedsono' : w.saleorder_.name ,'Soqty' : w.saleorder_.poqty , 'Dispqty' : w.saleorder_.dispatchqty , 'Balanceqty' : w.saleorder_.balanceqty}
        # elif woname:
            # for w in woname:
                # dic[w.id] = { 'Wono' : w.name, 'Woprogresshtml' : w.woprogresscompact , 'customer' : w.saleorder_.party_.name,'partno' : w.item_.name, 'Woqty':w.tqty ,'linkedsono' : w.saleorder_.name ,
                                  # 'Soqty' : w.saleorder_.poqty , 'Dispqty' : w.saleorder_.dispatchqty , 'Balanceqty' : w.saleorder_.balanceqty}        
        # elif soname:
            # for w in soname:
                # dic[w.id] = { 'Wono' : w.name, 'Woprogresshtml' : w.woprogresscompact , 'customer' : w.saleorder_.party_.name,'partno' : w.item_.name, 'Woqty':w.tqty ,'linkedsono' : w.saleorder_.name ,
                                  # 'Soqty' : w.saleorder_.poqty , 'Dispqty' : w.saleorder_.dispatchqty , 'Balanceqty' : w.saleorder_.balanceqty}       
        # else:
            # _logger.info("*********")
        # _logger.info(dic)
        return json.dumps(dic,default=date_utils.json_default)
        
    
    
        
   
class Wobom(models.Model):
    _name = 'simrp.wobom'
    
    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    wostate = fields.Selection( related='wo_.state' )
    bomitem_ = fields.Many2one( 'simrp.item', 'Required Item', readonly = True )

    bomuom_ = fields.Many2one('simrp.uom', related='bomitem_.uom_')
    bomqty = fields.Float( 'Content', digits=(8,5), readonly = True )

    #planning flag
    
    requiredqty = fields.Float( 'Qty Required', digits=(8,2), compute='_requiredqty' )
    issueqty = fields.Float( 'Issue', digits=(8,2), compute='_issueqty' )
    toutput = fields.Float( 'T.output', digits=(8,2), compute='_toutput' )
    consumed = fields.Float( 'Consumed', digits=(8,2), compute='_consumed' )
    balance = fields.Float( 'At Process', digits=(8,2), compute='_balance' )

    _rec_name = 'bomitem_'

    def generatewopo( self ):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.porder',
            'target': 'new',
            # 'res_id': o.id,
            'context': {
                'default_item_': self.bomitem_.id, 
                'default_poqty': self.requiredqty,
                'default_wo_': self.wo_.id,
                'form_view_initial_mode': 'edit', 
                'force_detailed_view': 'true'},
            }
    
    @api.multi
    @api.depends( 'wo_', 'bomqty' )
    def _requiredqty(self):    
        for o in self:
            o.requiredqty = o.bomqty * o.wo_.tqty
            
    @api.multi
    @api.depends( 'wo_', 'wo_.woissue_s', 'wo_.woissue_s.iqty' )
    def _issueqty(self):    
        for o in self:
            q = 0
            for i in o.wo_.woissue_s:
                if i.wobom_.id == o.id:
                    q = q + i.iqty
            o.issueqty = q
    
    @api.multi
    @api.depends( 'issueqty', 'bomitem_', 'bomqty', 'wo_', 'wo_.woissue_s', 'wo_.woissue_s.iqty' )
    def _toutput(self):  
        for o in self:
            o.toutput = o.issueqty / o.bomqty
    
    @api.multi
    @api.depends( 'bomitem_', 'bomqty', 'wo_', 'wo_.woissue_s', 'wo_.woissue_s.iqty' )
    def _consumed(self):  
        for o in self:
            q = 0
            for m in o.wo_.womfg_s:
                q = q + m.okqty + m.rejqty
            o.consumed = q * o.bomqty

    @api.multi
    @api.depends( 'bomitem_', 'bomqty', 'wo_', 'wo_.woissue_s', 'wo_.woissue_s.iqty' )
    def _balance(self):  
        for o in self:
            o.balance = o.issueqty - o.consumed
            
    
    @api.multi
    def issue( self ):
        self.env[ 'simrp.woissue' ].create( {
            'wo_': self.wo_.id, 
            'wobom_': self.id, 
            'item_': self.bomitem_.id,
            'iqty': self.requiredqty
        } )
        return True
    

    
class Woissue(models.Model):
    _name = 'simrp.woissue'
    
    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    wobom_ = fields.Many2one( 'simrp.wobom', 'Wobom', readonly = True )
    item_ = fields.Many2one( 'simrp.item', 'Item', related='wobom_.bomitem_' )
    idate = fields.Date( 'Issue date', default=lambda self: fields.Date.today(), readonly = True )
    lotno = fields.Char( 'Manual Lot no', size = 200 )
    iqty = fields.Float( 'Iqty', digits=(8,2), required = True )
    
class Woprocess(models.Model):
    _name = 'simrp.woprocess'
    
    name = fields.Char( 'Woprocess', size = 20, readonly = True )
    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    woitem_ = fields.Many2one( 'simrp.item', 'Item', readonly = True )
    wostate = fields.Selection( related='wo_.state' )
    
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess', readonly = True )
    allowsubcon = fields.Boolean( related='itemprocess_.allowsubcon' )
    
    speed = fields.Float('Speed / hour', digits=(8,3), readonly = True )
    tqtytoprocess = fields.Integer( 'T.qty', readonly = True )
    
    ppokqty = fields.Integer( 'Ok qty', compute='_ppokqty' )
    pprejqty = fields.Integer( 'Rej qty', compute='_pprejqty' )
    balqty = fields.Integer( 'Bal qty', compute='_balqty' )
    balancehours = fields.Integer( 'Balance hours', compute='_balancehours' )
    planqty = fields.Integer( 'Planned qty', compute='_planqty' )
    
    woproduction_s = fields.One2many( 'simrp.woproduction', 'woprocess_', 'Woproduction', readonly = True )
    wotool_s = fields.One2many( 'simrp.wotool', 'woprocess_', 'Wotools', readonly = True )
    #TODO estimated primary byproduct qty
    
    _order = 'wo_'
    @api.multi
    @api.depends( 'woproduction_s', 'woproduction_s.okqty' )
    def _ppokqty(self):  
        for o in self:
            q = 0
            for p in o.woproduction_s:
                q = q + p.okqty
            for s in o.wo_.subcondc_s:
                if s.itemprocess_.id == o.itemprocess_.id:
                    q = q + s.outputexpected - s.balanceqtyo
            o.ppokqty = q

    @api.multi
    @api.depends( 'woproduction_s', 'woproduction_s.rejqty' )
    def _pprejqty(self):  
        for o in self:
            q = 0
            for p in o.woproduction_s:
                q = q + p.rejqty
            for s in o.wo_.subcondc_s:
                if s.itemprocess_.id == o.itemprocess_.id:
                    for g in s.grn_s:
                        q = q + g.rejinqty
            o.pprejqty = q

    @api.multi
    @api.depends( 'woproduction_s', 'woproduction_s.okqty', 'tqtytoprocess' )
    def _balqty(self):  
        for o in self:
            o.balqty = o.tqtytoprocess - o.ppokqty

    @api.multi
    def _planqty(self):  
        for o in self:
            q = 0
            for p in o.woproduction_s:
                if p.state in [ 'p', 's' ]:
                    q = q + p.planqty
            for s in o.wo_.subcondc_s:
                if s.itemprocess_.id == o.itemprocess_.id:
                    q = q + s.outputexpected
            o.planqty = q
            
    @api.multi
    @api.depends( 'woproduction_s', 'woproduction_s.okqty', 'tqtytoprocess', 'speed' )
    def _balancehours(self):  
        for o in self:
            o.balancehours = -1
            if o.speed > 0:
                o.balancehours = o.balqty / o.speed
        
    @api.multi
    def generatewoproduction( self ):
        o = self.env[ 'simrp.woproduction' ].create( { 'woprocess_': self.id } )
        o.planhrs_change()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.woproduction',
            'target': 'current',
            'res_id': o.id,
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'},
            }

    @api.multi
    def generatewoproductionsetup( self ):
        o = self.env[ 'simrp.woproduction' ].create( { 'woprocess_': self.id, 'processmode': 's', 'planhrs': 0 } )
        o.planhrs_change()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.woproduction',
            'target': 'current',
            'res_id': o.id,
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'},
            }

    @api.multi
    def generatewoproductionrework( self ):
        o = self.env[ 'simrp.woproduction' ].create( { 'woprocess_': self.id, 'processmode': 'r', 'planhrs': 4 } )
        o.planhrs_change()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.woproduction',
            'target': 'current',
            'res_id': o.id,
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'},
            }
            
    
class Wotool(models.Model):
    _name = 'simrp.wotool'
    
    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    woprocess_ = fields.Many2one( 'simrp.woprocess', 'Woprocess', readonly = True )
    item_ = fields.Many2one('simrp.item', 'Item', readonly = True )
    expectedlife = fields.Float('Expected Tool life', readonly = True )
    pqty = fields.Integer( 'Producted Qty', compute="_pqty" )
    tconsumed = fields.Integer( 'Tool Corners consumed', compute='_tconsumed' )
    achievedlife = fields.Float( 'Achievedlife', digits=(8,2), compute='_achievedlife' )
    
    wotoolconsume_s = fields.One2many( 'simrp.wotoolconsume', 'wotool_', 'Wotoolconsume', readonly = True )
    
    @api.multi
    @api.depends( 'wo_' )
    def _pqty(self):  
        for o in self:
            q = 0
            for p in o.woprocess_.woproduction_s:
                q = q + p.okqty + p.rejqty
            o.pqty = q
            
    @api.multi
    @api.depends( 'wo_' )
    def _tconsumed(self):  
        for o in self:
            q = 0
            for p in o.wotoolconsume_s:
                q = q + p.wotoolqty
            o.tconsumed = q    

    @api.multi
    @api.depends( 'wo_' )
    def _achievedlife(self):  
        for o in self:
            o.achievedlife = -1
            if o.tconsumed > 0:
                o.achievedlife = o.pqty / o.tconsumed
            

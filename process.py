# -*- coding: utf-8 -*-

import difflib
import datetime
from odoo import api, fields, models, exceptions
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import xmlrpc.client
import logging
_logger = logging.getLogger(__name__)
        
class Bom(models.Model):
    _name = 'simrp.bom'
    
    item_ = fields.Many2one('simrp.item', 'Item', required=True)
    bomitem_ = fields.Many2one('simrp.item', 'BOM Input', required=True)
    bomuom_ = fields.Many2one('simrp.uom', 'UOM', related='bomitem_.uom_')
    # bomqty = fields.Float( 'BOM Qty/product', digits=(8,5), required = True, default=1)
    bomqty = fields.Float( 'BOM Qty/product', digits=(8,5), compute='_bomqty')
    bomqtyold = fields.Float( 'BQOld', digits=(8,5), readonly = True )
    active = fields.Boolean(default=True)
    t = fields.Char( 'T', size=100 )

    spgrlist = {'ms': 0.00786, 'ss': 0.00780, 'al': 0.00270, 'cu': 0.00889, 'br': 0.00850, 'ab': 0.00744, 'pl': 0.00150}
    @api.depends( 't' )
    def _bomqty( self ):
        for o in self:
            r = 0
            
            if o.t:
                try:
                    t = o.t + ',0,0,0,0,0,0'
                    ts = t.split(',')
                    shape = ts[ 0 ].strip()
                    mv = ts[ 1 ].strip()
                    v1 = float( ts[ 2 ].strip() )
                    v2 = float( ts[ 3 ].strip() )
                    v3 = float( ts[ 4 ].strip() )
                    v4 = float( ts[ 5 ].strip() )
                    
                    if shape == 'd':
                        r = float( mv )
                    else:
                        spgr = self.spgrlist[ mv ]
                        a = 0
                        if shape == 'r':
                            a = 3.142857 * v1 * v1 / 4
                            r = spgr * a * ( v2 + v3 ) / 1000
                        elif shape == 'p':
                            a = 3.142857 * ( ( v1 * v1 ) - ( v2 * v2 ) ) / 4
                            r = spgr * a * ( v3 + v4 ) / 1000
                        elif shape == 'h':
                            a = 0.866 * v1 * v1
                            r = spgr * a * ( v2 + v3 ) / 1000
                        elif shape == 'f':
                            a = v1 * v2
                            r = spgr * a * ( v3 + v4 ) / 1000
                except:
                    o.help()
            o.bomqty = r

    def help( self ):
        raise exceptions.UserError( 'Round: r, <mat>, od, len, len+\nPipe: p, <mat>, od, id, len, len+\nHex: h, <mat>, af, len, len+\nRectangle: f, <mat>, H, W, len, len+\nDirect: d, weight-in-kg\n\n<mat> options:\n\nms: MS / Alloy steel (0.00786)\nss: Stainless Steel (0.00780)\nal: Aluminum (0.00270)\ncu: Copper (0.00889)\nbr: Brass (0.00850)\nab: Aluminum Bronze (0.00744)\npl: Plastic (0.00150)\n\nExample: r, ms, 20, 55, 5\nExample: p, br, 20, 15, 30, 3\nExample: d, 0.00120' )

class ProcessType(models.Model):
    _name = 'simrp.processtype'
    _description = 'Process Type'
    
    name = fields.Char('Process Type', required=True)
    des = fields.Char('Description')
        
class ItemProcess(models.Model):
    _name = 'simrp.itemprocess'
    _description = 'Item Process'

    item_ = fields.Many2one('simrp.item', 'Item')

    name = fields.Char(compute='_xname', store=True)
    seq = fields.Integer('Seq#', required=True)
    processtype = fields.Many2one('simrp.processtype', 'Process Type', required=True)       #process type RM / CNC / HT ..
    des = fields.Char('Description')
    cycletime = fields.Float('Cycle Time (sec)', digits=(8,2) )
    loadtime = fields.Integer('Load Time (sec)')
    loadper = fields.Integer('Loading every (pcs)', default=1)
    speed = fields.Float('Speed / hour', compute='_speed', store=True)
    iofile_s = fields.One2many( 'simrp.iofile', 'itemprocess_', 'Item Files' )
    qaplandate = fields.Date('QA Plan Date', readonly=True, default=lambda self: fields.Date.today())
    qaplanrev = fields.Integer('QA Plan Revision', default=0, readonly=True)
    # log = fields.Text('QA Revision History', default='0 - New')
    
    allowsubcon = fields.Boolean('Subcontract?', default=False)
    subcon = fields.One2many('simrp.processsubcon', 'itemprocess_', 'Subcontracting Details')

    byproduct = fields.One2many('simrp.processbyproduct', 'itemprocess_', 'Process Byproducts')
    setupinst = fields.One2many('simrp.processsetupinst', 'itemprocess_', 'Setup Instructions')
    operinst = fields.One2many('simrp.processoperinst', 'itemprocess_', 'Operating Instructions')
    toollist = fields.One2many('simrp.processtool', 'itemprocess_', 'Tools Data')
    qadetails = fields.One2many('simrp.processqap', 'itemprocess_', 'QA Control Plan')
    active = fields.Boolean( default = True )
    
    shortname = fields.Char( 'Shortname', compute='_shortname' )
    state = fields.Selection([('d', 'Modification'), ('a', 'Reviewed')], default='d', readonly = True )
    log = fields.Text( 'Log', readonly = True )
    lasttranscript = fields.Text( 'Lasttranscript', readonly = True )

    changeitem_ = fields.Many2one('simrp.item', 'Shift to Item')

    _order = 'seq'

    def iotsync( self ):
        if self.env.cr.dbname in [ 'shahauto', 'jia' ]:
            # url = 'http://jiaiot.vii.co.in:8169'
            # db = 'jiaiot'
            # uname = 'k'
            # passw = 'dr90210#!$'
            url = 'http://vii.co.in:8300'
            db = 'iiot12test'
            uname = 'phpconnect'
            passw = 'sics@#admin1234'
            token = 'AWei25v'
            # url = 'http://127.0.0.1:8169'
            # db = 'bunts'
            # uname = 'k'
            # passw = 'sics@#$admin'
            
            common = xmlrpc.client.ServerProxy( url + '/xmlrpc/2/common')
            uid = common.authenticate( db, uname, passw, {} )
            models = xmlrpc.client.ServerProxy( url + '/xmlrpc/2/object')

            idmul = 1
            if self.env.cr.dbname == 'shahauto':
                idmul = -1
                
            idict = { 'erpid': idmul * self.item_.id, 'name': self.item_.dwg_no, 'shortname': self.item_.des }
            ptdict = { 'erpid': idmul * self.processtype.id, 'name': self.processtype.name, 'des': self.processtype.des }
            pdict = { 'erpid': idmul * self.id, 'seq': self.seq, 'cycletime': self.cycletime, 'loadtime': self.loadtime / self.loadper,
                            'speedtype': 'c', 'cavity': 1, 'cntresolution': 1, 'des': self.des }
            qadict = {}
            for qad in self.qadetails:
                insname = ''
                if qad.instrumentcategory_:
                    insname = qad.instrumentcategory_.name
                if qad.insrumentcode:
                    if qad.insrumentcode.dwg_no:
                        insname += qad.insrumentcode.dwg_no
                qadict[ str(idmul * qad.id) ] = { 'erpid': idmul * qad.id, 'param': qad.param, 'type': qad.type, 'low': qad.low, 'high': qad.high,
                                            'freq': qad.freq, 'insrumentname': insname, 'react': qad.react }

            setupdict = {}
            for si in self.setupinst:
                setupdict[ str(idmul * si.id) ] = { 'erpid': idmul * si.id, 'name': si.name, 'type': si.type, 'low': si.low, 'high': si.high }
            operdict = {}
            for oi in self.operinst:
                operdict[ str(idmul * oi.id) ] = { 'erpid': idmul * oi.id, 'name': oi.name }

            d = { 'idict': idict, 'ptdict': ptdict, 'pdict': pdict, 'qadict': qadict, 'setupdict': setupdict, 'operdict': operdict }
            rid = models.execute_kw( db, uid, passw, 'iiot12.iiot', 'syncprocess', [ -1, token, d ] )
            
            _logger.info( '################# PROCESS SYNC: ' + str(rid) )
        return True


    def approve(self):
        self.updateTranscript()
        # self.item_.updateTranscript()
        self.state = 'a'
        return True

    def modify(self):
        self.state = 'd'
        return True

    def transcribe( self ):
        o = self
        l = "|ITEM|" + o.item_.name + "\n|NAME| " + o.name + "\n|SUBC| " + str(o.allowsubcon) + "\n|REV.| " + str( o.qaplanrev ) + ' dt. ' + o.qaplandate.strftime( DEFAULT_SERVER_DATE_FORMAT ) + "\n"
        l = l + "|SPED| Mc: " + str( o.cycletime ) + ' Lt: ' + str( o.loadtime ) + ' / ' + str( o.loadper ) + ' (' + str( o.speed ) + ' /hr)\n-----\n'
        for i in self.subcon:
            l = l + "|SUBC| [" + str(i.code) +"] " + str(i.party_.name) + " @ " + str(i.rate) + "/" + str(i.rateuom_.name) + " 1=> " + str(i.uomconv) +", policy: "+ str(i.scrappolicy) + '\n'
        l = l + '-----\n'
        for i in self.qadetails:
            l = l + "|ocpp| " + str(i.param) + " #T " + i.typename() + " #L " + str(i.low) + " #H " + str(i.high) + " #F " + i.freqname() + '\n'
        l = l + '-----\n'
        for i in self.toollist:
            l = l + "|TOOL| " + i.item_.name + " @ " + str(i.expectedlife) + "\n"
        for i in self.setupinst:
            l = l + "|SETP| " + i.name + " #T " + i.type + " #L " + str(i.low) + " #H " + str(i.high) + "\n"
        for i in self.operinst:
            l = l + "|OPER| " + i.name + "\n"
        l = l + '-----\n'
        for i in self.byproduct:
            l = l + "|BYPR| " + str( i.qty ) + " " + i.item_.name + "\n"
        return l

        
    def updateTranscript( self ):
        self.qaplandate = fields.Date.today()
        self.qaplanrev = self.qaplanrev + 1
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

    def shiftitem( self ):
        self.item_ = self.changeitem_.id
        self.changeitem_ = False
        
    def _shortname( self ):
        for o in self:
            a = ''
            if o.allowsubcon:
                a = '**'
            o.shortname = '[' + str( o.seq ) + '-' + o.processtype.name + a + ']'
            
    @api.multi
    @api.depends('seq', 'processtype', 'des', 'qaplanrev')
    def _xname(self):
        for o in self:
            r = ''
            seq = ''
            des = ''
            # qaplanrev = ''
            processtype = ''
            if o.processtype:
                processtype = o.processtype.name
            if o.des:
                des = o.des
            if o.seq:
                seq = str( o.seq );
            # if o.qaplanrev:
                # qaplanrev = o.qaplanrev
            r = '[' + seq + '-' + processtype + '] ' + des + ' (rev. ' + str( o.qaplanrev ) + ')'
            o.name = r

    @api.multi
    @api.depends('cycletime', 'loadtime', 'loadper')
    def _speed(self):
        for o in self:
            ltperpiece = o.loadtime
            if o.loadper > 1:
                ltperpiece = o.loadtime / o.loadper
            netCT = o.cycletime + ltperpiece
            o.speed = 0
            if netCT > 0:
                o.speed = round( 3600 / netCT, 2 )

    @api.model
    def qadetails15html(self):
        i = 0
        s = ''
        limit = 18
        for qap in self.qadetails:
            i = i + 1
            if i == (limit+1):
                break
            s = s + '<tr><td class="text-left small pt-1">[' + qap.typename() + '] ' + qap.param
            s = s + '</td><td class="text-left small pt-1">' + str( qap.low )
            s = s + ' / ' + str( qap.high )
            s = s + '</td><td class="text-left small pt-1">' + qap.freqname()
            s = s + '</td><td class="text-left small pt-1">' + qap.instrumentcategory_.name
            if qap.insrumentcode:
                s = s + ' [' + qap.insrumentcode.dwg_no + ']'
            s = s + '</td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-left small pt-1">' + qap.react
            s = s + '</td></tr>'
        if i < limit:
            for x in range( i, limit ):
                s = s + '<tr><td class="text-left small pt-1">.'
                s = s + '</td><td class="text-left small pt-1">'
                s = s + '</td><td class="text-left small pt-1">'
                s = s + '</td><td class="text-left small pt-1">'
                s = s + '</td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-right"></td><td class="text-left small pt-1">'
                s = s + '</td></tr>'
        return s

    @api.model
    def qadetailshtml(self):
        i = 0
        s = ''
        limit = 18
        for qap in self.qadetails:
            i = i + 1
            if i == (limit+1):
                break
            s = s + '<tr><td class="text-left small pt-1">[' + qap.typename() + '] ' + qap.param
            s = s + '</td><td class="text-left small pt-1">' + str( qap.low )
            s = s + ' / ' + str( qap.high )
            s = s + '</td><td class="text-left small pt-1">' + qap.freqname()
            s = s + '</td><td class="text-left small pt-1">' + qap.instrumentcategory_.name
            if qap.insrumentcode:
                s = s + ' [' + qap.insrumentcode.dwg_no + ']'
            s = s + '<td class="text-left small pt-1">' + qap.react
            s = s + '</td></tr>'
        return s

    @api.model
    def subconhtml(self):
        i = 0
        s = ''
        limit = 5
        for qap in self.subcon:
            i = i + 1
            if i == (limit+1):
                break
            s = s + '<tr><td class="text-left small pt-1">' + qap.code
            s = s + '</td><td class="text-left small pt-1">' + qap.party_.name 
            s = s + '</td><td class="text-left small pt-1">' + str( qap.opconv )
            s = s + '</td><td class="text-left small pt-1">' + str( qap.moq )
            s = s + '</td><td class="text-left small pt-1">' + str ( qap.rate )
            s = s + '</td><td class="text-right">' + qap.rateuom_.name
            s = s + '</td><td class="text-right">' + str ( qap.uomconv )
            s = s + '</td><td  style="font-size:10px" class="text-left small pt-1">' + qap.explain
            if qap.scrappolicy == 'nr':
                s = s + '</td><td class="text-left small pt-1">' + 'Not Returnable'
            else:
                s = s + '</td><td class="text-left small pt-1">' + ' Returnable '
            s = s + '</td></tr>'
        return s

    @api.model
    def byproducthtml(self):
        i = 0
        s = ''
        limit = 4
        for qap in self.byproduct:
            i = i + 1
            if i == (limit+1):
                break
            s = s + '<tr><td class="text-left small pt-1">' + qap.item_.name
            s = s + '</td><td class="text-left small pt-1">' + str( qap.qty )
            s = s + '</td></tr>'
        if i < limit:
            for x in range( i, limit ):
                s = s + '<tr><td class="text-left small pt-1">.'
                s = s + '</td><td class="text-left small pt-1">'
                s = s + '</td></tr>'
        return s

class ProcessSubcon(models.Model):
    _name = 'simrp.processsubcon'
    _description = 'Subcontracted Process Agreement'

    #name = fields.Char(compute='_xname', store=True)
    code = fields.Char('Agreement Code', readonly=True)
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process', readonly = True )
    inputitem_ = fields.Many2one('simrp.item', 'Input item', required = True )
    item_ = fields.Many2one( related='itemprocess_.item_' )
    byproductitem_ = fields.Many2one('simrp.item', 'Byproduct' )
    
    party_ = fields.Many2one('simrp.party', 'Subcontractor', required=True)
    moq = fields.Integer('MOQ')
    rate = fields.Float('Rate', required=True)
    since = fields.Date( 'Since', default=datetime.date.today() )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Tax Scheme', required = True ) 
    log = fields.Text( 'Log', readonly = True )
    active = fields.Boolean(default=True, readonly=True)
    inputuom_ = fields.Many2one( 'simrp.uom', 'Input UOM', related='inputitem_.uom_' )
    outputuom_ = fields.Many2one( 'simrp.uom', 'Output UOM', related='item_.uom_' )
    byproductuom_ = fields.Many2one( 'simrp.uom', 'By-product UOM', related='byproductitem_.uom_' )

    opconv = fields.Float('x Conversion', digits=(8,5), default=1, required=True)
    byconv = fields.Float('x By-product', digits=(8,5) )
    value = fields.Float( 'Value ', digits=(8,2), compute='_value' )
    rateuom_ = fields.Many2one( 'simrp.uom', 'Party Rate UOM', required = True, default=1 )
    uomconv = fields.Float('Oty / rate uom', digits=(8,5), default=1, required=True)
    scrappolicy = fields.Selection([
        ('r', 'Returnable'),
        ('nr', 'Non-Returnable'),
        ], 'Scrap Policy', default='nr', required=True)
    transport = fields.Selection( [
            ( 'o', 'Only One way delivery paid by us' ),
            ( 'r', 'Only One way return paid by us' ),
            ( 'b', 'Delivery and return paid by us' ),
            ( 'f', 'Delivery and return paid by you' ),            
            ], 'Transport', default='b' )
    explain = fields.Text( 'Explanation', compute="_explain" )

    wostate = fields.Char( compute='_wostate' )

    _rec_name = 'code'
    
    def _wostate( self ):
        if 'wost' in self.env.context:
            for o in self:
                o.wostate = self.env.context[ 'wost' ]
        
    @api.depends('inputitem_', 'item_', 'byproductitem_', 'opconv', 'byconv', 'rateuom_', 'uomconv')
    def _explain(self):
        for o in self:
            s = ""
            if ( o.inputitem_ and o.item_ ):
                if ( o.inputuom_.id != o.outputuom_.id ) or ( o.opconv != 1 ) or ( o.inputitem_.id != o.item_.id ):
                    s = "1 " + o.inputuom_.name + " of (" + o.inputitem_.name + ") will generate " + str( o.opconv ) + " " + o.outputuom_.name + " of (" + o.item_.name + "). "
                else:
                    s = o.inputuom_.name + " based. "
            if ( o.byproductitem_ and o.item_ ):
                s = s + "and every " + o.outputuom_.name + " of (" + o.item_.name + ") will generate " + str( o.byconv ) + " " + o.byproductuom_.name + " of (" + o.byproductitem_.name + "). "
            if ( o.rateuom_ and o.item_ ):
                s = s + "Party will bill in " + o.rateuom_.name
                if o.uomconv != 1:
                    s = s + " ( 1 " + o.rateuom_.name + " = " + str( o.uomconv ) + " " + o.outputuom_.name + " )"
            o.explain = s
    
    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('simrp.subcon')
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Create: ' + o.explain, o.read( [ 'code', 'party_', 'item_', 'itemprocess_', 'taxscheme_', 'rate', 'opconv'  ] )[0], True, False )
        return o

    def write(self, vals):
        if 'log' not in vals:
            self.env[ 'simrp.auditlog' ].log( self, 'Change:', vals, True, True )
        return super().write(vals)
        
    @api.multi
    def generatesubcondc( self ):
        o = self.env[ 'simrp.subcondc' ].create( { 'processsubcon_': self.id } )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.subcondc',
            'target': 'current',
            'res_id': o.id,
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'},
            }

#            'context': self.env.context,
#            'target': 'new',
#            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}, 'initial_mode': 'edit'}
#            'name': _('Change Destination Location'),
#            'views': [(view.id, 'form')],
#            'view_id': view.id,
    
    @api.multi
    def _value(self):
        for o in self:
            if o.rate > 0:
                o.value = o.uomconv / o.rate

    @api.multi
    def reactivate(self):
        self.active = True
        return True

    @api.multi
    def unactivate(self):
        self.active = False
        return True
    
class ProcessByproduct(models.Model):
    _name = 'simrp.processbyproduct'
    _description = 'Process Byproduct'
    
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process', required=True)
    item_ = fields.Many2one('simrp.item', 'Item', required=True, domain="[('type', '=', 'scrap'), ('state', '=', 'a')]")
    qty = fields.Float('Qty / unit', digits=(8,4) )

class ProcessSetupinst(models.Model):
    _name = 'simrp.processsetupinst'
    _description = 'Process Setup Instructions'
    
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process', required=True)
    name = fields.Char('Instruction', required=True)
    type = fields.Selection([
        ('a', 'Attribute (Ok/NotOk)'),
        ('m', 'Measurable'),
        ], 'Instruction Type', default='a', required=True)
    low = fields.Float('Lower limit', digits=(8,4) )
    high = fields.Float('Upper limit', digits=(8,4) )

class ProcessOperinst(models.Model):
    _name = 'simrp.processoperinst'
    _description = 'Process Operation Instructions'
    
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process', required=True)
    name = fields.Char('Instruction', required=True)

class ProcessTool(models.Model):
    _name = 'simrp.processtool'
    _description = 'Process Tooling'
    
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process', required=True)
    item_ = fields.Many2one('simrp.item', 'Item', required=True, domain="[('type', 'in', ['equipment','cons','insert']), ('state', '=', 'a')]")
    expectedlife = fields.Float('Expected Tool life')

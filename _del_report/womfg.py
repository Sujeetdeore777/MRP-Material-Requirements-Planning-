# -*- coding: utf-8 -*-

import datetime, time, pytz, json
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import shiftinfo


class Woproduction(models.Model):
    _name = 'simrp.woproduction'
    
    name = fields.Char( 'Woproduction', size = 20, readonly = True, default='<draft>' )
    woprocess_ = fields.Many2one( 'simrp.woprocess', 'Woprocess', readonly = True )
    wo_ = fields.Many2one( related='woprocess_.wo_' )
    itemprocess_ = fields.Many2one( related='woprocess_.itemprocess_' )
    item_ = fields.Many2one( related='itemprocess_.item_' )
    item_shortname = fields.Char( related='item_.shortname' )

    machine_ = fields.Many2one( 'simrp.machine', 'Machine' )
    employee_ = fields.Many2one( 'simrp.employee', 'Operator' )
    #setupemployee_ = fields.Many2one( 'simrp.employee', 'Setup Operator' )                     Culture Change
    planqty = fields.Float( 'Planned Qty', digits=(5,2), default=0 )
    planhrs = fields.Float( 'Planned Hours', digits=(5,2), default=11.5 )
    
    state = fields.Selection( [
            ( 'd', 'Draft'),
            ( 'p', 'Plan' ),
            ( 's', 'Start' ),
            ( 'q', 'Data Update' ),
            # ( 'a', 'CIA Pending' ),
            ( 'c', 'Closed' ),
            ], 'State', default='d' )
    
    processmode = fields.Selection( [
            ( 'p', 'Production'),
            ( 's', 'Setup' ),
            ( 'r', 'Rework' ),
            ], 'Process Mode', default='p', readonly=True )
    pmodestr = fields.Char( 'Pmodestr', compute='_pmodestr' )

    plantimestamp = fields.Integer( 'Priority', default=1 )

    datamode = fields.Selection( [
            ( 'a', 'Auto'),
            ( 'm', 'Manual' ),
            ], 'Data Mode', default='a', readonly=True )
    
    itspeed = fields.Float( related='woprocess_.speed' )

    fpaemployee_ = fields.Many2one( 'simrp.employee', 'FPA Operator' )

    pstime = fields.Datetime( 'Start', readonly = True )
    petime1 = fields.Datetime( 'End', digits=(4,4) )
    
    apdtime = fields.Integer( 'Down (mins)', default=0 )
    prodtime = fields.Integer( 'Time (mins)', digits=(8,2), compute="_prodtime", store=True )
    qcemployee_ = fields.Many2one( 'simrp.employee', 'QC Certified by' )
    
    okqty = fields.Integer( 'Ok qty' )
    rejqty = fields.Integer( 'Rej qty' )                  #Reject qty criteria for inspection and analysis
    # tspeed = fields.Float( 'Tspeed', digits=(8,2), readonly = True )    #archive point of time
    aspeed = fields.Float( 'Aspeed', digits=(8,2), compute="_prodtime", store=True )
    p = fields.Float( 'Productivity %', digits=(8,2), compute="_prodtime", store=True )
    q = fields.Float( 'Quality %', digits=(8,2), compute="_prodtime", store=True )
    
    wobyproduct_s = fields.One2many( 'simrp.wobyproduct', 'woproduction_', 'Wobyproduct' )
    wotoolconsume_s = fields.One2many( 'simrp.wotoolconsume', 'woproduction_', 'Tool Consumptions' )

    submittime = fields.Datetime( 'Submit Time', readonly = True )

    #These fields removed from logic
    sstime = fields.Datetime( 'Setup Start', readonly = True )
    setime = fields.Float( 'End (24h)', digits=(4,4) )    
    setime1 = fields.Datetime( 'Setup End' )
    asdtime = fields.Integer( 'S.Down (mins)', default=0 )
    # setuptime = fields.Integer( 'Setup (mins)', digits=(8,2), compute="_setuptime", store=True )
    setuptime = fields.Integer( 'Setup (mins)', digits=(8,2) )
    sokqty = fields.Integer( 'Setup Ok qty', default=0 )
    srejqty = fields.Integer( 'Setup Rej qty', default=0 )
    # adate1 = fields.Date( 'Prod Date', compute="_adate", store=True )
    adate1 = fields.Date( 'Prod Date' )
    petime = fields.Float( 'End (24h)', digits=(4,4) )
    pokqty = fields.Integer( 'Prod. Ok qty', default=0 )
    prejqty = fields.Integer( 'Prod. Rej qty', default=0 )
    # totalqty = fields.Integer( 'Total qty', compute="_totalqty", store=True )
    totalqty = fields.Integer( 'Total qty' )

    _order = 'pstime desc, plantimestamp'

    @api.onchange('planhrs')
    def planhrs_change(self):
        if self.planhrs >= 0:
            self.planqty = self.itspeed * self.planhrs

    def _pmodestr( self ):
        modedict = { 'p':'Production', 's':'Setup',  'r':'Rework' }        
        for o in self:
            o.pmodestr = modedict[ o.processmode ]
            
    # @api.multi
    # @api.depends( 'sstime', 'pstime' )
    # def _adate( self ):
        # for o in self:
            # if o.sstime:
                # tzsstime = o.sstime + datetime.timedelta( seconds=19800 )
                # o.adate1 = tzsstime.date()
                # if tzsstime.hour < 8:           #8 am
                    # o.adate1 = o.adate1 + datetime.timedelta( days=-1 )
    
    # @api.multi
    # @api.depends( 'setime1', 'asdtime' )
    # def _setuptime( self ):
        # for o in self:
            # if o.sstime:
                # #if ( o.setime >= 24 ) or ( o.setime < 0 ):
                # #    raise exceptions.UserError( 'End time is incorrect' )
                # o.setuptime = shiftinfo.getShiftTimeDiff2( o.sstime, o.setime1, self.env.user.tz, o.asdtime, True )
    
    @api.depends( 'pstime', 'petime1', 'apdtime', 'okqty', 'rejqty' )
    def _prodtime( self ):
        for o in self:
            if o.pstime and o.petime1:
                #if ( o.petime >= 24 ) or ( o.petime < 0 ):
                #    raise exceptions.UserError( 'End time is incorrect' )
                # _logger.info( ">>>>>>>>>>>>>>>>>>>PS>>>> " + str( o.pstime ) );
                o.prodtime = shiftinfo.getShiftTimeDiff2( o.pstime, o.petime1, self.env.user.tz, o.apdtime, True )
                # _logger.info( ">>>>>>>>>>>>>>>>>>>P>>>> " + str( o.prodtime ) );
                a = 0
                if o.prodtime > 0:
                    a = ( o.okqty + o.rejqty ) / ( o.prodtime / 60 )
                o.aspeed = a
                r = 0
                if o.itspeed and o.itspeed > 0:
                    r = ( o.aspeed / o.itspeed ) * 100
                if r > 100:
                    r = 100
                o.p = r
                r = 0
                if o.okqty > 0:
                    r = ( o.okqty / (o.okqty + o.rejqty) ) * 100
                if r > 100:
                    r = 100
                o.q = r
            
    # @api.multi
    # @api.depends( 'sokqty', 'pokqty' )
    # def _okqty( self ):
        # for o in self:
            # o.okqty = o.sokqty + o.pokqty
            
    # @api.multi
    # @api.depends( 'srejqty', 'prejqty' )
    # def _rejqty( self ):
        # for o in self:
            # o.rejqty = o.srejqty + o.prejqty
            
    # @api.multi
    # @api.depends( 'sokqty', 'pokqty', 'srejqty', 'prejqty' )
    # def _totalqty( self ):
        # for o in self:
            # o.totalqty = o.okqty + o.rejqty
            
    # @api.model
    # def localtime( self, t ):
        # return shiftinfo.getlocaltime( t, self.env.user.tz )
        
    @api.multi
    def plan(self):
        if not self.machine_:
            raise exceptions.UserError( 'Machine name is empty' )
        if not self.employee_:
            raise exceptions.UserError( 'Operator name is empty' )
            
        if self.processmode in [ 'p', 'r' ]:
            if self.planqty <= 0:
                raise exceptions.UserError( 'Check Plan qty' )
            if self.itspeed <= 0:
                raise exceptions.UserError( 'Process Target speed not defined' )
        
        #blank tool consumption records
        for t in self.woprocess_.wotool_s:
            self.env[ 'simrp.wotoolconsume' ].create( { 'wotool_': t.id, 'woproduction_': self.id } )
        #blank byproduct record
        for b in self.itemprocess_.byproduct:
            self.env[ 'simrp.wobyproduct' ].create( { 'woproduction_': self.id, 'item_': b.item_.id, 'qtyper': b.qty } )

        self.name = self.env['ir.sequence'].next_by_code('simrp.woproduction')
        self.state = 'p'
        
        self.plantimestamp = time.time()
        self.planhrs_change()
        return True

    def replan(self):
        self.state = 'p'
        return True

    @api.multi
    def start(self):
        ntnow = fields.Datetime.now()
        self.starttime( ntnow )
        return True

    @api.multi
    def starttime( self, ntnow ):
        #nt = shiftinfo.getlocaltime( ntnow, self.env.user.tz )
        # self.sstime = ntnow
        self.pstime = ntnow
        # self.setime1 = ntnow
        # self.employee_.inPanel()
        
        self.state = 's'
        return True
    
    @api.multi
    def getqctableandon(self, machineid):
        #search all start record
        datadictionary = {}
        tableschedules = {}
        startproduction = {}
        controlplan = {}
        startrecords = self.env[ 'simrp.woproduction' ].search( [ ('machine_', '=', machineid), ('state', '=', 's' ) ] )
        if not startrecords:
            planrecords = self.env[ 'simrp.woproduction' ].search( [ ('machine_', '=', machineid), ('state', '=', 'p' ) ] )
            if planrecords:
                k = 0
                for p in planrecords:
                    _logger.info("***********Plan"+str(p.id))
                    tablesch = {}
                    tablesch2 = {}
                    tablesch['id'] = p.id
                    tablesch['prcode'] = p.name
                    tablesch['Part'] = p.item_.name
                    tablesch['qty'] = p.planqty
                    tablesch['Operator'] = p.employee_.name
                    tablesch['machineid'] = p.machine_.id
                    tablesch['machinename'] = p.machine_.name
                    tablesch['targetspeed'] = p.itemprocess_.speed
                    tablesch2 = {str(k): tablesch}
                    tableschedules.update(tablesch2)
                    k = k + 1
        run_once = 0
        if startrecords:
            for s in startrecords:
                k1 = 0
                if run_once == 0:
                    _logger.info("***********Start"+str(s.id))
                    startprod = {}
                    startprod2 = {}
                    qa = {}
                    qa2 = {}
                    startprod['id'] = s.id
                    startprod['prcode'] = s.name
                    startprod['Part'] = s.item_.name
                    startprod['starttime'] = str(s.pstime)
                    startprod['qty'] = s.planqty
                    startprod['Operator'] = s.employee_.name
                    startprod['machineid'] = s.machine_.id
                    startprod['machinename'] = s.machine_.name
                    startprod['targetspeed'] = s.itemprocess_.speed
                    startprod2 = {str(k1): startprod}
                    startproduction.update(startprod2)
                    processqap = self.env[ 'simrp.processqap' ].search( [ ('itemprocess_', '=', s.itemprocess_.id) ] )
                    if processqap:
                        k = 0
                        for q in processqap:
                            _logger.info("***********processqap"+str(q.id))
                            qa = {}
                            qa['id'] = q.id
                            qa['param'] = q.param
                            qa['category'] = q.instrumentcategory_.name
                            qa['freq'] = q.freq
                            qa2 = {str(k): qa}
                            controlplan.update(qa2)
                            k = k + 1
                    run_once = run_once + 1
                    k1 = k1 + 1
        datadictionary ={ 
            'tableschedules' : tableschedules,
            'partheader' : startproduction,
            'controlplan' : controlplan
        }
        return datadictionary

    @api.multi
    def startqctableinspection(self, machineid, prid):
        o = self.env[ 'simrp.woproduction' ].search( [ ('machine_', '=', machineid), ('id', '=', prid) ] )
        o.start()
        return True

    @api.multi
    def submitqctableinspection(self, machineid, prid, jsondata, viiqty):
        o = self.env[ 'simrp.woproduction' ].search( [ ('machine_', '=', machineid), ('id', '=', prid) ] )
        data = json.loads(jsondata)
        # data = {
              # "r1" : {
                # "id" : "2",
                # "rejqty" : 5
              # },
              # "r2" : {
                # "id" : "3",
                # "rejqty" : 10
              # },
              # "r3" : {
                # "id" : "1",
                # "rejqty" : 2
              # }
            # }
        srej = 0
        prej = 0
        for key in data:
            prej = prej + data[key]['rejqty']
        pok = int(viiqty) - prej
        o.closePR(srej, prej, pok)
        res = self.env[ 'simrp.tinitinspection' ].create( {
                'item_': o.item_.id,
                'itemprocess_': o.itemprocess_.id,
                'lotqty': viiqty
            } )
        res.initz()
        qcid = res['res_id']
        qc = self.env['simrp.qcinspection'].search( [ ('id', '=', qcid) ] )
        qcidetails = self.env['simrp.qcidetails'].search( [ ('qcinspection_', '=', qcid) ] )
        for q in qcidetails:
            for key in data:
                if q.processqap_id == data[key]['id']:
                    rejcnt = data[key]['rejqty']
                    if rejcnt > 0:
                        q.rejectcount = data[key]['rejqty']
                        q.remarks = "Auto:Firewall"
                    elif rejcnt < 0:
                        q.result = True
        qcid.submit()


    @api.multi
    def closePR(self, srej, prej, pok):
        self.asdtime = 0
        # self.sokqty = 0
        # self.srejqty = srej
        self.petime1 = fields.Datetime.now()

        self.apdtime = 0
        self.okqty = pok
        self.rejqty = prej + srej
        self.qcemployee_ = self.employee_.id

        self.submit()

        return True

    def submit(self):
        # if self.prodtime == 0:
            # raise exceptions.UserError( 'Production Time is 0. Cannot submit.' )
            
        self.submittime = fields.Datetime.now()
        self.state = 'q'
        
        #record byproduct expected qty and stock
        for b in self.wobyproduct_s:
            b.pqty = b.qtyper * ( self.okqty + self.rejqty )
            if b.pqty > 0:
                if b.aqty == 0:
                    b.aqty = b.pqty
                if self.wo_.type == 'n':
                    s = self.env[ 'simrp.stock' ].create( { 'okinqty': b.pqty } )
                    s.initStock( b.item_, 'simrp.woproduction', self.id, False )
        
        return True

    def qc(self):
        #if self.totalqty == 0:
        #    raise exceptions.UserError( 'All production quantities are zero. Cannot submit.' )

        # if (not self.fpaemployee_) or ( not self.qcemployee_ ):
            # raise exceptions.UserError( 'FPA certification or QC certification missing' )

        # if ( self.rejqty <= 2 ):
        self.state = 'c'
        # else:
            # self.state = 'a'
        return True

    # @api.multi
    # def analysed(self):                                             # RCA and tasks linkage
        # self.state = 'c'
        # return True

    @api.multi
    def cancelPR( self ):
        if self.totalqty != 0:
            raise exceptions.UserError( 'All quantities not zero' )
        self.sudo().unlink()
        action = self.env.ref('simrp.simrp_wo_action').read()[0]
        return action

    @api.multi
    def printpr(self):
        return self.env.ref('simrp.action_report_printpr').report_action(self)


class Twoproduction(models.TransientModel):
    _name = 'simrp.twoproduction'

    woproduction_ = fields.Many2one( 'simrp.woproduction' )
    stime = fields.Datetime( 'Start Record', default=lambda self: fields.Datetime.now() )
    
    @api.multi
    def start( self ):
        self.woproduction_.starttime( self.stime )
        self.woproduction_.datamode = 'm'
        return { 'type': 'ir.actions.act_view_reload' }

class Wotoolconsume(models.Model):
    _name = 'simrp.wotoolconsume'
    
    woproduction_ = fields.Many2one( 'simrp.woproduction', 'Woproduction', readonly = True )
    wo_ = fields.Many2one( related='woproduction_.wo_' )
    woprocess_ = fields.Many2one( related='woproduction_.woprocess_' )
    totalqty = fields.Integer( related='woproduction_.okqty' )

    wotool_ = fields.Many2one( 'simrp.wotool', 'Tool', readonly = True )
    item_ = fields.Many2one( related='wotool_.item_' )
    expectedlife = fields.Float( related='wotool_.expectedlife' )
    wotoolqty = fields.Integer( 'Qty edges consumed', default=0 )    

class Wobyproduct(models.Model):
    _name = 'simrp.wobyproduct'
    
    woproduction_ = fields.Many2one( 'simrp.woproduction', 'Woproduction', readonly = True )
    wo_ = fields.Many2one( related='woproduction_.wo_' )
    woprocess_ = fields.Many2one( related='woproduction_.woprocess_' )
    
    item_ = fields.Many2one('simrp.item', 'Item', readonly = True )
    qtyper = fields.Float('Qty / unit', digits=(8,4), readonly = True )
    pqty = fields.Float( 'Exepected Qty', digits=(8,2), readonly = True )
    aqty = fields.Float( 'Actual Qty', digits=(8,2) )
    
    
class Womfg(models.Model):
    _name = 'simrp.womfg'
    
    name = fields.Char( 'Womfg', size = 50, readonly = True )
    mfgdate = fields.Date( 'Mfgdate', default=lambda self: fields.Date.today(), readonly = True )

    wo_ = fields.Many2one( 'simrp.wo', 'Wo', readonly = True )
    mfgitem_ = fields.Many2one( 'simrp.item', 'Item', related='wo_.item_' )

    okqty = fields.Integer( 'Okqty' )
    rejqty = fields.Integer( 'Rejqty' )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.womfg')
        o = super(Womfg, self).create(vals)
        
        return o
    
    @api.multi
    def initStock( self ):
        for o in self:
            q = o.okqty + o.rejqty

            # consumption of BOM items
            for bi in o.wo_.wobom_s:
                #consume bi stock q * bi.bomqty
                s = self.env[ 'simrp.stock' ].create( { 'okoutqty': q * bi.bomqty, } )
                s.initStock( bi.bomitem_, 'simrp.womfg', o.id, False )

            # create stock entries FG
            s = self.env[ 'simrp.stock' ].create( { 'okinqty': o.okqty, 'rejinqty': o.rejqty } )
            s.initStock( o.mfgitem_, 'simrp.womfg', o.id, False )
        
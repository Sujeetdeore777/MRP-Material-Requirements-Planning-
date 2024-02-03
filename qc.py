# -*- coding: utf-8 -*-

import datetime, time
from odoo import api, fields, models, exceptions 
from . import shiftinfo
import logging
_logger = logging.getLogger(__name__)

class Qcinspection(models.Model):
    _name = 'simrp.qcinspection'
    
    name = fields.Char( 'Inspection Code', size = 10, readonly = True )
    idate = fields.Datetime( 'Inspection Submit Time', readonly = True, default=lambda self: fields.Datetime.now() )
    cdate = fields.Datetime( 'Inspection Decision Time', readonly = True )
    
    item_ = fields.Many2one('simrp.item', 'Item', readonly = True )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess', readonly = True )
    grn_ = fields.Many2one( 'simrp.grn', 'Grn', readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Party', readonly = True )
    lotqty = fields.Float( 'Lot Qty', readonly = True )
    
    sampleqty = fields.Integer( 'AQL Qty c0/d0.40%', compute='_sampleqty' )
    qcidetails_s = fields.One2many( 'simrp.qcidetails', 'qcinspection_', 'Parameters' )

    okqty = fields.Float( 'Ok Qty', readonly = True )
    rejqty = fields.Float( 'Rej Qty', readonly = True )

    stage = fields.Selection([
        ('grn', 'GRN'),
        ('set', 'Setting'),
        ('in', 'Inprocess'),
        # ('c', 'Customer'),
        ], 'Stage', default='grn', required = True, readonly=True )
    
    state = fields.Selection( [
            ( 'p', 'Pending' ),
            ( 'i', 'Quality Issue' ),
            ( 'ok', 'Inspected OK' ),
            ( 'dok', 'Deviation / Sorting' ),
            ( 'rej', 'Lot Rejected' ),
            ], 'State', readonly = True, default='p' )
            
    accstate = fields.Selection( [
            ( 'p', 'Pending' ),
            ( 'r', 'Review' ),
            ( 'ne', 'No Impact' ),
            ( 'rd', 'Recover' ),
            ], 'Acc. Status', readonly = True, default='p' )
    log = fields.Text( 'Log', readonly = True, default='' )
    debit_ = fields.Many2one( 'simrp.debit', 'Rejection Debit Note', readonly = True )
    
    _order = 'create_date desc'
    
    def reset( self ):
        if self.accstate != 'rd':
            self.state = 'p'
        
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('simrp.qcinspection')
        o = super(Qcinspection, self).create(vals)
        if o.grn_:
            o.party_ = o.grn_.party_.id
        return o
        
    def _sampleqty( self ):
        #c=0, zero based sampling, defect rate at 0.40%
        for o in self:
            q = self.lotqty
            s = 189
            if q <= 500000:
                s = 156
            if q <= 150000:
                s = 123
            if q <= 35000:
                s = 108
            if q <= 10000:
                s = 86
            if q <= 3200:
                s = 74
            if q <= 500:
                s = 48
            if q <= 280:
                s = 32
            if s > o.lotqty:
                s = o.lotqty
            o.sampleqty = s
        
    @api.multi
    def initQCI(self):
        qaps = self.itemprocess_.qadetails
        for qap in qaps:
            param = qap.param
            if qap.type in [ 'm','mspc','msc' ]:
                param = param + " [" + str( qap.low ) + " / " + str( qap.high ) + "]"
            else:
                param = param + " [ ok / not-ok ]"
            ins = qap.instrumentcategory_.name if qap.instrumentcategory_ else ""
            ins = ins + ( ( "[" + qap.insrumentcode.name + "]" ) if qap.insrumentcode else "" )
            self.env[ 'simrp.qcidetails' ].create( {
                'processqap_': qap.id,
                'param': param,
                'method': ins,
                'qcinspection_': self.id,
            } )
        # self.sampleqty = self.getsamplesize( self.lotqty )
        return True
        
        
    @api.multi
    def submit(self):
        r = 'ok'
        l = ""
        v = True
        for qci in self.qcidetails_s:
            if qci.result == False:
                r = 'i'
                if qci.remarks == "":
                    v = False
                else:
                    l = l + qci.param + ": " + qci.remarks + "\r\n"
            else:
                if qci.rejectcount > 0:
                    raise exceptions.UserError('Rejected qty parameter marked as ok')
        if not v:
            raise exceptions.UserError('All Rejected Parameters should have remarks')
        self.state = r
        if r == 'ok':
            l = shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "] Lot found OK\r\n"
            self.cdate = fields.Datetime.now()
            self.okqty = self.lotqty
            self.rejqty = 0
            self.accstate = 'ne'
        else:
            l = shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "] Lot not Satisfactory. Awaiting Manager Decision.\r\n" + l
            self.okqty = 0
            self.rejqty = self.lotqty
            if self.grn_:
                if self.grn_.purchase_:
                    if self.grn_.purchase_.state in [ 's', 'a' ]:
                        self.grn_.purchase_.draft1()
                        self.grn_.purchase_.state = 'd'
        if not self.log:
            self.log = ""
        self.log = self.log + l
        if self.grn_:
            self.grn_.okinqty = self.okqty
            self.grn_.rejinqty = self.rejqty
            self.grn_.qcstate = r
            self.grn_.checkClose()
        return True

    @api.model
    def debit(self, ar ):
        if not self.party_:
            raise exceptions.UserError('Party to be selected')
        self.accstate = 'rd'
        rr = self.env[ 'simrp.debit' ].create( {
                'qcinspection_': self.id,
                'ar': ar + "\r\n\r\n" + self.log,
                'party_': self.party_.id
        } )
        self.debit_ = rr
        self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "] Accounts Recovery Posted.\r\n" + ar + "\r\n"
        return True

    @api.multi
    def norecover(self):
        self.accstate = 'ne'
        self.log = self.log + shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "] Cleared w/o Accounts Recovery.\r\n"
        return True
        
    @api.model
    def deleteqci( self ):
        o = self
        if o.accstate == 'rd':
            raise exceptions.UserError('QC Inspection already linked to a Debit Note. Cannot Delete')
        for qd in o.qcidetails_s:
            qd.unlink()
        o.unlink()
    
    
class Qcidetails(models.Model):
    _name = 'simrp.qcidetails'
    
    qcinspection_ = fields.Many2one( 'simrp.qcinspection', 'Qcinspection', readonly = True )
    item_ = fields.Many2one('simrp.item', related='qcinspection_.item_' )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', related='qcinspection_.itemprocess_' )
    
    idate = fields.Datetime( related='qcinspection_.idate' )
    lotqty = fields.Float( related='qcinspection_.lotqty' )
    processqap_ = fields.Many2one( 'simrp.processqap', 'Process Parameter', readonly = True )
    qapparam = fields.Char( related='processqap_.param' )
    
    param = fields.Char('Parameter [Low/High]', readonly = True )
    method = fields.Char('Method (Instrument)', readonly = True )
    result = fields.Boolean( 'Result', default=False )
    remarks = fields.Text( 'Remarks', default="" )
    rejectcount = fields.Float( 'R Count' )
    
    _order = 'id desc'
    #failtype = fields.Selection([
    #    ('l', 'Lesser than lower limit'),
    #    ('u', 'Higher than upper limit'),
    #    ('gx', 'Go / Ok not answering'),
    #    ('ngx', 'NO-GO / Not-Ok answering'),
    #    ('a', 'Absent / Operation missing'),
    #    ('o', 'Other'),
    #    ], 'Type', default='i', required=True)

    @api.multi
    def resultstatus(self):
        if self.result:
            self.result = False
        else:
            self.result = True
        return True

class Tqcinspectionupdate(models.TransientModel):
    _name = 'simrp.tqcinspectionupdate'
    
    qcinspection_ = fields.Many2one( 'simrp.qcinspection', 'Qcinspection', readonly = True )
    log = fields.Text( 'Log', related='qcinspection_.log' )    
    addremarks = fields.Char( 'Remarks', required = True )

    @api.multi
    def update(self):
        self.qcinspection_.log = self.qcinspection_.log + shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "] " + self.addremarks + "\r\n"
        return { 'type': 'ir.actions.act_view_reload' }

class Tqcinspectiondecide(models.TransientModel):
    _name = 'simrp.tqcinspectiondecide'
    
    qcinspection_ = fields.Many2one( 'simrp.qcinspection', 'Qcinspection', readonly = True )
    log = fields.Text( 'Log', readonly = True )    
    addremarks = fields.Char( 'Remarks', required = True )
    state = fields.Selection( [
            ( 'ok', 'Inspected OK' ),
            ( 'dok', 'Deviation / Sorting' ),
            ( 'rej', 'Lot Rejected' ),
            ], 'State', required = True, default='rej' )
    item_ = fields.Many2one('simrp.item', 'Item', related='qcinspection_.item_' )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess', related='qcinspection_.itemprocess_' )
    lotqty = fields.Float( 'Lot Qty', related='qcinspection_.lotqty' )
    okqty = fields.Float( 'Ok Qty' )
    rejqty = fields.Float( 'Rej Qty' )

    @api.multi
    def update(self):
        for qcid in self.qcinspection_.qcidetails_s:
            if not qcid.result:
                if ( qcid.remarks == "" ) or ( not qcid.rejectcount ):
                    raise exceptions.UserError('Enter Remarks and Rejection Count against each NotOk Parameter')
        if self.state == 'dok':
            if self.okqty + self.rejqty != self.lotqty:
                raise exceptions.UserError('For deviation, Ok qty + Rej Qty should be equal to Lot qty.')
            self.qcinspection_.okqty = self.okqty
            self.qcinspection_.rejqty = self.rejqty
            self.qcinspection_.accstate = 'r'
        elif self.state == 'ok':
            # raise exceptions.UserError('Here')
            self.qcinspection_.okqty = self.lotqty
            self.qcinspection_.rejqty = 0
            self.qcinspection_.accstate = 'ne'
        else:
            self.qcinspection_.okqty = 0
            self.qcinspection_.rejqty = self.lotqty
            self.qcinspection_.accstate = 'r'
        self.qcinspection_.log = self.qcinspection_.log + shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "]  " + self.addremarks + "\r\n"
        self.qcinspection_.state = self.state        
        self.qcinspection_.cdate = fields.Datetime.now()
        if self.qcinspection_.grn_:
            self.qcinspection_.grn_.qcstate = self.state
            self.qcinspection_.grn_.okinqty = self.qcinspection_.okqty
            self.qcinspection_.grn_.rejinqty= self.qcinspection_.rejqty
            self.qcinspection_.grn_.checkClose()
            if ( self.rejqty > 0 )  and ( self.qcinspection_.grn_.purchase_ ):
                if self.qcinspection_.grn_.purchase_.state in [ 's', 'a' ]:
                    self.qcinspection_.grn_.purchase_.draft1()
                    self.qcinspection_.grn_.purchase_.state = 'd'
        return { 'type': 'ir.actions.act_view_reload' }

class Tqcinspectionrecover(models.TransientModel):
    _name = 'simrp.tqcinspectionrecover'
    
    qcinspection_ = fields.Many2one( 'simrp.qcinspection', 'Qcinspection', readonly = True )
    log = fields.Text( 'Log', related='qcinspection_.log' )    
    addremarks = fields.Text( 'Remarks', required = True, default='What (item):\r\nQty:\r\nDebit Rate:\r\nOther Debits:\r\nSupply Document:\r\nReason:' )
    
    @api.multi
    def update(self):
        self.qcinspection_.debit( self.addremarks )
        return { 'type': 'ir.actions.act_view_reload' }

class Tinitinspection(models.TransientModel):
    _name = 'simrp.tinitinspection'
    
    item_ = fields.Many2one('simrp.item', 'Item', required = True )
    itemprocess_ = fields.Many2one( 'simrp.itemprocess', 'Itemprocess', required = True )
    lotqty = fields.Float( 'Lot Qty', required = True )
    stage = fields.Selection([
        ('grn', 'RM'),
        ('set', 'Setting'),
        ('in', 'Inprocess'),
        ], 'Stage', default='in', required = True )

    processqap_ = fields.Many2one( 'simrp.processqap', 'Process Parameter' )
    remarks = fields.Text( 'Remarks' )

    @api.multi
    def initz( self ):
        if self.lotqty <= 0:
            raise exceptions.UserError('Lot Qty should be > 0')
        qci = self.env['simrp.qcinspection'].create( { 
                                'item_': self.item_.id, 
                                'itemprocess_': self.itemprocess_.id, 
                                'lotqty': self.lotqty,
                                'stage': self.stage
                                } )
        qci.initQCI()

        if self.processqap_:
            for qcid in qci.qcidetails_s:
                if qcid.processqap_.id == self.processqap_.id:
                    qcid.result = False
                    qcid.remarks = self.remarks
                    qcid.rejectcount = self.lotqty
                else:
                    qcid.result = True
                    qcid.remarks = 'Not Checked (rej record)'
            qci.okqty = 0
            qci.rejqty = self.lotqty
            qci.log = shiftinfo.getnowlocaltimestring( self ) + "[" + self.env.user.name + "] Parameter Rejection Recorded. Awaiting Manager Decision.\r\n"
            qci.state = 'rej'
            qci.norecover()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'simrp.qcinspection',
            'target': 'current',
            'res_id': qci.id,
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'},
            }

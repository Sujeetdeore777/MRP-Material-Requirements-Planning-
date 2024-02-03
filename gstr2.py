# -*- coding: utf-8 -*-

import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.tools as tools

import logging
_logger = logging.getLogger(__name__)
from xlrd import open_workbook
import base64
import io

class Gstr2(models.Model):
    _name = 'simrp.gstr2'

    name = fields.Date( 'Ref. Date of GSTR2', default=lambda self: fields.Date.today(), required = True )
    store = fields.Binary( 'File', attachment=True )
    storename = fields.Char( 'Name' )
    notes = fields.Char( 'Desc' )
    log = fields.Text( 'Log', readonly = True, default="" )

    gstr2line_s = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True )
    gstr2line_s_um = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('match','=','-'),('itcavailable','=',True)] )
    gstr2line_s_ignored = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('match','=','x')] )

    gstr2line_s_um_b2b = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('type','=','b2b'),('match','=','-'),('itcavailable','=',True)] )
    gstr2line_s_um_b2b_noitc = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('type','=','b2b'),('itcavailable','=',False)] )
    gstr2line_s_b2ba = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('type','=','b2ba'),('match','=','-')] )
    gstr2line_s_b2bc = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('type','=','b2bc'),('match','=','-')] )
    gstr2line_s_b2bca = fields.One2many( 'simrp.gstr2line', 'gstr2_', 'Details', readonly = True, domain=[('type','=','b2bca'),('match','=','-')] )
    state = fields.Selection( [
            ( 'i', 'Init' ),
            ( 'p', 'Imported' ),
            ], 'State', readonly = True, default='i' )

    def getreportpath( self ):
        return self.env['ir.config_parameter'].sudo().get_param('reportpath') or tools.config['addons_path']

    def importfile(self):
        o = self
        if not o.store:
            raise exceptions.ValidationError( 'File not selected' )
        
        try:
            inputx = io.BytesIO()
            inputx.write( base64.decodestring( o.store ) )
            book = open_workbook( file_contents = inputx.getvalue() )
            o.log = o.log + '\r\nLoading file: ' + o.storename + ' ... '
        except TypeError as e:
            raise exceptions.ValidationError( 'ERROR: {}' . format( e ) )
        
        f = '/simrp/gstr2.ix.py'
        cmd = ""

        with open( o.getreportpath() + f, 'r') as file:
            cmd = file.read()
        exec( cmd )
        
        o.log = o.log + 'Done'
        o.store = False
        o.storename = False
        # o.state = 'p'
                
    def dummy( self ):
        return True
        
    @api.multi
    def process(self):
        for o in self:
            totallines = 0
            prevmatch = 0
            newmatch = 0
            unmatch = 0
            purchases = self.env[ 'simrp.purchase' ].search( [ ( 'gstr2state','=','n'), ( 'state', '=', 'a' ) ] )
            # expenses = self.env[ 'simrp.indirectexpense' ].search( [ ( 'gstr2state','=','n'), ( 'state', '=', 'a' ) ] )
            for gl in o.gstr2line_s:
                if ( gl.type == 'b2b' ) and ( gl.itcavailable == True ) :
                    totallines = totallines + 1
                    if gl.match == '-':
                        check = 0
                        for p in purchases:
                            if ( p.party_.gstno == gl.gstin ) and ( p.gstr2state == 'n' ) and ( abs( p.matchnet - gl.invval ) < 4 ) and ( ( p.docno == gl.invno ) or ( p.docdate == datetime.datetime.strptime( gl.invdt, '%d/%m/%Y').date() ) ) and ( abs( p.taxamount - gl.totgst ) < 1 ):
                                newmatch = newmatch + 1
                                check = 1
                                gl.match = 'a'
                                p.gstr2state = 'a'
                                p.gadjreason = str( o.id ) + " / " + gl.invno + " / " + str( gl.totgst )
                                break
                        # if check == 0:
                            # for p in expenses:
                                # if ( p.party_.gstno == gl.gstin ) and ( p.gstr2state == 'n' ) and ( abs( p.netamount - gl.invval ) < 4 ) and ( ( p.docno == gl.invno ) or ( p.docdate == datetime.datetime.strptime( gl.invdt, '%d-%m-%Y').date() )  ) and ( abs( p.taxamount - gl.totgst ) < 1 ):
                                    # newmatch = newmatch + 1
                                    # check = 1
                                    # gl.match = 'a'
                                    # p.gstr2state = 'a'
                                    # p.gadjreason = o.storename + " / " + gl.invno + " / " + str( gl.totgst )
                                    # break
                            
                        if check == 0:
                            unmatch = unmatch + 1
                    else:
                        prevmatch = prevmatch + 1
            # if not o.log:
                # o.log = ""
            o.log = o.log + '\r\nNew Match: ' + str( newmatch ) + ', Unmatched: ' + str( unmatch ) + ', Prev. Matched: ' + str( prevmatch ) + ', Total B2B lines: ' + str( totallines )
            
class Gstr2line(models.Model):
    _name = 'simrp.gstr2line'
    _order = "gstin, type, invno"
    
    gstr2_ = fields.Many2one( 'simrp.gstr2', 'Gstr2', readonly = True )
    type = fields.Selection( [
            ( 'b2b', 'B2B' ),
            ( 'b2ba', 'B2BA' ),
            ( 'b2bc', 'B2B-CDNR' ),
            ( 'b2bca', 'B2B-CDNRA' ),
            ], 'Type', readonly = True )    
            
    gstin = fields.Char( 'Gstin', size = 20, readonly = True )
    gstname = fields.Char( 'Gstname', size = 100, readonly = True )
    invno = fields.Char( 'Inv No', size = 30, readonly = True )
    invdt = fields.Char( 'Invdt', size = 12 )
    invval = fields.Float( 'Invoice Value', digits=(8,2), readonly = True )
    totgst = fields.Float( 'GST Amount', digits=(8,2), readonly = True )
    itcavailable = fields.Boolean( 'ITC', readonly = True )
    itcreason = fields.Char( 'Itcreason', size = 200, readonly = True )

    oinvno = fields.Char( 'Orig Inv No', size = 30, readonly = True )
    oinvdt = fields.Char( 'Invdt', size = 12 )
    doctype = fields.Char( 'Doctype', size = 30, readonly = True )

    match = fields.Selection( [
            ( '-', '-' ),
            ( 'x', 'Ignore' ),
            ( 'a', 'ok' ),
            ], 'Match', readonly = True, default='-' )    
    
    purchase_s = fields.One2many( 'simrp.purchase', compute='_purchase_s' )
    purchase_ = fields.Many2one( 'simrp.purchase', 'Lucky match', compute='_purchase_' )

    purchase_docno = fields.Char( related='purchase_.docno' )
    purchase_docdate = fields.Date( related='purchase_.docdate' )
    purchase_matchnet = fields.Float( related='purchase_.matchnet' )
    purchase_taxamount = fields.Float( related='purchase_.taxamount' )

    @api.one
    def _purchase_s(self):
        r = self.env[ 'simrp.purchase' ].search( [ ( 'party_.gstno','=',self.gstin ), ( 'gstr2state','in',['n','x']) ] )
        self.purchase_s = r
        
    def ignore(self):
        for o in self:
            o.match = 'x'

    def unignore(self):
        for o in self:
            o.match = '-'
            
    def _purchase_(self):
        for o in self:
            idt = o.invdt.replace( "-", "/" )
            r = self.env[ 'simrp.purchase' ].search( [ ( 'party_.gstno','=',o.gstin ), ( 'gstr2state','=','n'), ( 'docdate','=',datetime.datetime.strptime( idt, '%d/%m/%Y').date() ), ( 'matchnet','>',o.invval - 4 ), ( 'matchnet','<',o.invval + 4) ] )
            if r:
                o.purchase_ = r[ 0 ]

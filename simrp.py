# -*- coding: utf-8 -*-

import datetime, time, pytz
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from . import shiftinfo
import xmlrpc.client

class Simrp(models.TransientModel):
    _name = 'simrp.simrp'

    def getPRlist( self ):
        pr = self.env[ 'simrp.woproduction' ].search( [ ( 'state','in',['p','s'] ) ] )
        prlist = []
        for p in pr:
            dp = { 'name': p.name, 'machine_': p.machine_.id, 'employee_': p.employee_.id, 'item_': p.item_.name, 'itemprocess_': p.itemprocess_.name, 'wo_': p.wo_.name, 'itspeed': p.itspeed, 'state': p.state, 'id': p.id, 'planqty': p.planqty, 'item_shortname': p.item_shortname, 'pstime': p.pstime, 'processmode': p.processmode, 'plantimestamp': p.plantimestamp, 'duration': 0 }
            if p.itspeed > 0:
                dp[ 'duration' ] = p.planqty / p.itspeed
            prlist.append( dp )
        return prlist
            
        
    def getLoadChart( self ):
        emps = self.env[ 'simrp.employee' ].search( [ ( 'type','=','p' ) ] )
        shahemp = {}
        for e in emps:
            shahemp[ e.shahsyncid ] = e.id

        _logger.info( shahemp )
        
        prlist = self.env[ 'simrp.simrp' ].getPRlist()

        url = 'http://shahauto.vii.co.in:8069'
        db = 'shahauto'
        uname = 'ks12mobile@gmail.com'
        passw = 'dr90210#!$'

        common = xmlrpc.client.ServerProxy( url + '/xmlrpc/2/common')
        uid = common.authenticate( db, uname, passw, {} )
        models = xmlrpc.client.ServerProxy( url + '/xmlrpc/2/object')

        prlist2 = models.execute_kw( db, uid, passw, 'simrp.simrp', 'getPRlist', [ -1 ] )

        for p in prlist2:
            if p[ 'employee_' ] in shahemp:
                p[ 'employee_' ] = shahemp[ p[ 'employee_' ] ]
                prlist.append( p )
                
        return prlist
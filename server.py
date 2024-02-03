# -*- coding: utf-8 -*-

import odoo
import shutil
import os
import json
import datetime
from odoo import api, fields, models, exceptions 
import logging
import xmlrpc.client

_logger = logging.getLogger(__name__)

def dump_db_manifest(cr):
    pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
    cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
    modules = dict(cr.fetchall())
    manifest = {
        'odoo_dump': '1',
        'db_name': cr.dbname,
        'version': odoo.release.version,
        'version_info': odoo.release.version_info,
        'major_version': odoo.release.major_version,
        'pg_version': pg_version,
        'modules': modules,
    }
    return manifest

class Server(models.TransientModel):
    _name = 'simrp.server'


    @api.model
    def backup( self ):
        dir = self.env['ir.config_parameter'].sudo().get_param('backuppath')
        if not dir:
            raise exceptions.UserError( 'backuppath not configured' )
        # dir = 'dbbackup_odoo//'
        #dir = 'c://temp//'
        fname = dir + 'odoodb_' + self.env.cr.dbname + '_' + datetime.datetime.now().strftime( '%m%d%Y_%H%M%S' ) + '.zip'
        stream = open( fname, 'wb')
        
        db_name = self.env.cr.dbname
        _logger.info('K DUMP DB: %s ', db_name)

        cmd = ['pg_dump', '--no-owner']
        cmd.append(db_name)

        with odoo.tools.osutil.tempdir() as dump_dir:
            filestore = odoo.tools.config.filestore(db_name)
            if os.path.exists(filestore):
                shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
            with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(dump_db_manifest(cr), fh, indent=4)
            cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
            odoo.tools.exec_pg_command(*cmd)
            odoo.tools.osutil.zip_dir(dump_dir, stream, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
        
        stream.close()
        return True
        
    # @api.model
    # def mergeIEXPUR( self ):
        # ies = self.env[ 'simrp.indirectexpense' ].search( [ ( 'state', '=', 'a' ) ] )
        # for ie in ies:
            # _logger.info( '################### IEXPUR: ' + ie.name )
            # pr = self.env[ 'simrp.purchase' ].create( {
                    # 'name': ie.name,
                    # 'docno': ie.docno,
                    # 'docdate': ie.docdate,
                    # 'pdate': ie.tdate,
                    # 'party_': ie.party_.id,

                    # 'matchnet': ie.netamount, 
                    # } )
                    
            # for ied in ie.indirectexpdeatil_s:
                # self.env[ 'simrp.directpurchase' ].create( {
                    # 'purchase_': pr.id,
                    # 'date': ie.docdate,
                    # 'des': ied.description,
                    # 'qty': ied.qty,
                    # 'rate': ied.rate,
                    # 'taxscheme_': ie.taxscheme_.id,
                    # 'expenseaccount_': ie.expenseaccount_.id,
                    # } )
                    
            # pr.accept()
            # pr.name = ie.name
            
            # ie.delete()
            
        # return True
        
    # @api.model
    # def tfunc1( self ):
        # recs = self.env[ 'simrp.bom' ].search( [ ('active','in',[True,False] ) ] )
        # for r in recs:
            # r.bomqtyold = r.bomqty
            # r.t = 'd, ' + str( r.bomqty )
           
        # return True
        
    # @api.model
    # def tfunc1( self ):
        # recs = self.env[ 'simrp.woproduction' ].search( [ ('state','not in', ['c'] ) ] )
        # for r in recs:
            # r.state = 'c'
        # recs = self.env[ 'simrp.wo' ].search( [ ('state','not in', ['c'] ) ] )
        # for r in recs:
            # r.state = 'c'
        # recs = self.env[ 'simrp.porder' ].search( [ ('state','not in', ['c'] ) ] )
        # for r in recs:
            # r.state = 'c'
        # return True
        
        
    # @api.model
    # def tfunc1( self ):
        # recs = self.env[ 'simrp.stock' ].search( [] )
        # for r in recs:
            # if r.ref:
                # if r.ref._name in [ 'simrp.subcondc', 'simrp.grn' ]:
                    # print( r.ref._name + ' ' + str( r.ref.id ) )
                    # r.ref.recdate = r.recdate
                    # r.ref.party_ = r.party_.id
                    # r.ref.item_ = r.item_.id
                    # r.ref.okinqty = r.okinqty
                    # r.ref.rejinqty = r.rejinqty
                    # r.ref.okoutqty = r.okoutqty
                    # r.ref.rejoutqty = r.rejoutqty
        # return True

    @api.model
    def shahemplsync( self ):
        emplock = self.env['ir.config_parameter'].sudo().get_param('employeesynclock') or False
        if emplock:
            raise exceptions.UserError( 'Cannot start employee sync from this DB' )

        url = 'http://shahauto.vii.co.in:8069'
        db = 'shahauto'
        uname = 'ks12mobile@gmail.com'
        passw = 'dr90210#!$'
        
        common = xmlrpc.client.ServerProxy( url + '/xmlrpc/2/common')
        uid = common.authenticate( db, uname, passw, {} )
        models = xmlrpc.client.ServerProxy( url + '/xmlrpc/2/object')

        emps = self.env[ 'simrp.employee' ].search( [] )
        for e in emps:
            rid = models.execute_kw( db, uid, passw, 'simrp.employee',
                            'syncemployee', [ -1, e.shahsyncid, e.code, e.name, e.bu_.id, e.gender, e.type, e.salarytype, e.workhours, e.active ] )
            if e.shahsyncid != rid:
                e.shahsyncid = rid
        emps = self.env[ 'simrp.employee' ].search( [ ( 'active','=',False ), ( 'shahsyncid','>',0 ) ] )
        for e in emps:
            rid = models.execute_kw( db, uid, passw, 'simrp.employee',
                            'syncemployee', [ -1, e.shahsyncid, e.code, e.name, e.bu_.id, e.gender, e.type, e.salarytype, e.workhours, e.active ] )
            if e.shahsyncid != rid:
                e.shahsyncid = rid
        return True

    # @api.model
    # def shahemplsynctest( self ):
        # emplock = self.env['ir.config_parameter'].sudo().get_param('employeesynclock') or False
        # if emplock:
            # raise exceptions.UserError( 'Cannot start employee sync from this DB' )

        # common = xmlrpc.client.ServerProxy('http://shahauto.vii.co.in:8069/xmlrpc/2/common')
        # uid = common.authenticate( 'shahauto', 'ks12mobile@gmail.com', 'dr90210#!$', {} )
        # models = xmlrpc.client.ServerProxy('http://shahauto.vii.co.in:8069/xmlrpc/2/object')

        # x = models.execute_kw( 'shahauto', uid, 'dr90210#!$', 'simrp.employee',
                            # 'syncemployee', [ -1, -1, 'CCCC', 'TT1', 1, 'm', 'a', 'm', 8, True ] )
        # _logger.info( '44444444444444444444444444444444444 x' )
        # _logger.info( x )
        # return True

        
    # @api.model
    # def tfunc1( self ):
        # alines = self.env[ 'simrp.accline' ].search( [] )
        # for a in alines:
            # t = 0
            # for aa in a.ref_.accline_s:
                # t = t + aa.amountdr - aa.amountcr
            # if abs( t ) > 0.02:
                # _logger.info( a.ref_.name )
        # return True        

    @api.model
    def tfunc1( self ):
        dns = self.env[ 'simrp.debit' ].search( [ ('name','in', [ 'DN-001740', 'DN-001739', 'DN-001738', 'DN-001737', 'DN-001736', 'DN-001735', 'DN-001734', 'DN-001733', 'DN-001732', 'DN-001731', 'DN-001730', 'DN-001729', 'DN-001728', 'DN-001727', 'DN-001726', 'DN-001725', 'DN-001724', 'DN-001723', 'DN-001722', 'DN-001721', 'DN-001720', 'DN-001719', 'DN-001718', 'DN-001717', 'DN-001716', 'DN-001715', 'DN-001714', 'DN-001713', 'DN-001712', 'DN-001711', 'DN-001710', 'DN-001709', 'DN-001708', 'DN-001707', 'DN-001706', 'DN-001705', 'DN-001704', 'DN-001703', 'DN-001702', 'DN-001701', 'DN-001700', 'DN-001699', 'DN-001698', 'DN-001697', 'DN-001696', 'DN-001695', 'DN-001694', 'DN-001693', 'DN-001692', 'DN-001691', 'DN-001690', 'DN-001689', 'DN-001688', 'DN-001687', 'DN-001686', 'DN-001685', 'DN-001684', 'DN-001683', 'DN-001682', 'DN-001681', 'DN-001680', 'DN-001679', 'DN-001678', 'DN-001677', 'DN-001676', 'DN-001675', 'DN-001674', 'DN-001673', 'DN-001672', 'DN-001671', 'DN-001670', 'DN-001669', 'DN-001668', 'DN-001667', 'DN-001666', 'DN-001665', 'DN-001664', 'DN-001663', 'DN-001662', 'DN-001661', 'DN-001660', 'DN-001659', 'DN-001658', 'DN-001657', 'DN-001656', 'DN-001655', 'DN-001654', 'DN-001653', 'DN-001652', 'DN-001651', 'DN-001650', 'DN-001649', 'DN-001648', 'DN-001647', 'DN-001646', 'DN-001645', 'DN-001644', 'DN-001643', 'DN-001642', 'DN-001641', 'DN-001640', 'DN-001639', 'DN-001638', 'DN-001637', 'DN-001636', 'DN-001635', 'DN-001634', 'DN-001633', 'DN-001632', 'DN-001631', 'DN-001630', 'DN-001629', 'DN-001628', 'DN-001627', 'DN-001626', 'DN-001625', 'DN-001624', 'DN-001623', 'DN-001622', 'DN-001621', 'DN-001620', 'DN-001619', 'DN-001618', 'DN-001617', 'DN-001616', 'DN-001615', 'DN-001614', 'DN-001613', 'DN-001612', 'DN-001611', 'DN-001610', 'DN-001609', 'DN-001608', 'DN-001607', 'DN-001606', 'DN-001605', 'DN-001604', 'DN-001603', 'DN-001602', 'DN-001601', 'DN-001600', 'DN-001599', 'DN-001598', 'DN-001597', 'DN-001596', 'DN-001595', 'DN-001594', 'DN-001593', 'DN-001592', 'DN-001591', 'DN-001590', 'DN-001589', 'DN-001588', 'DN-001587', 'DN-001586', 'DN-001585', 'DN-001584', 'DN-001583', 'DN-001582', 'DN-001581', 'DN-001580', 'DN-001579', 'DN-001578', 'DN-001577', 'DN-001576', 'DN-001575', 'DN-001574', 'DN-001573', 'DN-001572', 'DN-001571', 'DN-001570', 'DN-001569', 'DN-001568', 'DN-001567', 'DN-001566', 'DN-001565', 'DN-001564', 'DN-001563', 'DN-001562', 'DN-001561', 'DN-001560', 'DN-001559', 'DN-001558', 'DN-001557', 'DN-001556', 'DN-001555', 'DN-001554', 'DN-001553', 'DN-001552', 'DN-001551', 'DN-001550', 'DN-001549', 'DN-001548', 'DN-001547', 'DN-001546', 'DN-001545', 'DN-001544', 'DN-001543', 'DN-001542', 'DN-001541', 'DN-001540', 'DN-001539', 'DN-001538', 'DN-001537', 'DN-001536', 'DN-001535', 'DN-001534', 'DN-001533', 'DN-001532', 'DN-001531', 'DN-001530' ] ) ] )
        
        for dn in dns:
            _logger.error( dn.name )
            # dn.delete()
        # alines = self.env[ 'simrp.accline' ].search( [ ('dispatch_','!=',False) ] )
        # idlist = []
        # for aline in alines:
            # idlist.append( aline.id )
            
        
        # areflines = self.env[ 'simrp.refadj' ].search( [ '|',('accline_','in',idlist),('agstaccline_','in',idlist) ] )
        # _logger.info( areflines )
        # areflines.unlink()
        
        # # alines.unlink()
        # # _logger.info( alines )
        
        
        # # dcs = self.env[ 'simrp.dispatch' ].search( [ ( 'invdate','>', datetime.date( 2022,9,30) )] )
        # dcs = self.env[ 'simrp.dispatch' ].search( [ ] )
        # for dc in dcs:
            # # if 'urch' in dc.saleorder_.taxscheme_.name:
                # # dc.saleorder_.taxscheme_ = dc.saleorder_.itemrate_.taxscheme_.id
            # r = 0
            # if dc.okoutqty > 0:
                # taxtot = dc.saleorder_.taxscheme_.compute( 1 )[ 'taxclass' ][ 'totalrate' ] / 100
                # r = ( ( dc.invamt / ( 1 + taxtot ) ) - dc.shippingcharge ) / dc.okoutqty
            # # _logger.info( dc.name + ' ' + str( r ) )
            # dc.rate = r
            # if ( not dc.invoice_ ) and (dc.state == 'i'):
                # inv = self.sudo().env[ 'simrp.invoice' ].create( {
                    # 'party_': dc.party_.id,
                    # 'shippingcharge': dc.shippingcharge,
                    # 'name': dc.name,
                    # 'invdate': dc.invdate,
                    # } )
                    
                # _logger.info( "***********" )
                # _logger.info( dc.name )
                # _logger.info( dc.dcno )
                
                # dc.name = dc.dcno
                # dc.invoice_ = inv.id
                # dc.state = 's'
                # inv.invoice()

                # for aline in dc.accline_s:
                    # aline.invoice_ = inv.id
                    # aline.dispatch_ = False
                    # aline.ref_ = '%s,%s' % ( 'simrp.invoice', inv.id )

                # inv.invamt = dc.invamt
                # inv.taxamt = dc.invamt - inv.basicamt
                
                # # if inv.invamt != dc.invamt:
                    # # dc.counthelp = 2
                # # for aline in dc.accline_s:
                    # # aline.delete()
                # # dc.accline_s.delete()
        return True        
        
    # @api.model
    # def tfunc1( self ):
        # return True        
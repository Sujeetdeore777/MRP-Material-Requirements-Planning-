# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, exceptions
    
class Party(models.Model):
    _name = 'simrp.party'
    _inherits = {'simrp.account': 'account_'} 

    account_ =  fields.Many2one( 'simrp.account', 'Account', required=True, ondelete="cascade")
    shortname = fields.Char('Short Name', size = 50)
    address1 = fields.Char(required=True)
    address2 = fields.Char()
    address3 = fields.Char()
    # scrapowner = fields.Boolean( 'Scrap Owner', default=False )
    pincode = fields.Char( required = True )
    email = fields.Char()
    mobile = fields.Text( 'Contact Nos.' )
    # smsmobile = fields.Char( 'SMS Contact No.' )
    vcode = fields.Char( 'Vendor Code', default='' )
    copies = fields.Integer( 'No. of invoice prints', default=2 )
    # firmtype = fields.Selection( [
            # ( 'i', 'Individual / Proprietor' ),
            # ( 'p', 'Partnership' ),
            # ( 'c', 'Company (pvt ltd / ltd)' ),
            # ], 'Firm Type', default='i' )
    owner = fields.Char( 'Owner', size = 200 )
    associate = fields.Selection( [
            ( 'TDS94Ci', '[TDS94Ci] Subcontractor / Repair / Maintenance - Individual / Proprietor' ),
            ( 'TDS94Cc', '[TDS94Cc] Subcontractor / Repair / Maintenance - Partnership / Company' ),
            ( 'TDS94Jt', '[TDS94Jt] Technical Consultation Services' ),
            ( 'TDS94Jp',  '[TDS94Jp] Legal and Professional Services' ),
            ( 'TDS94Hi', '[TDS94Hi] Brokerage / Comission Services' ),
            ( 'TDS94I', '[TDS94I] Rent Charges' ),
            ( 'lt', 'Local Transporter' ),
            ( 'sr', 'Supplier - RM' ),
            ( 'st', 'Supplier - Tooling' ),
            ( 'so', 'Supplier - Misc Consumables' ),
            ( 'cust', 'Customer' ),
            ( 'bank', 'Bank' ),
            ], 'Association, tds' )
    tdsdeduct = fields.Boolean( 'TDS Deduct', default=False )
    creditperiod = fields.Integer( 'PayTerms (days)', default=7 )

    state_ = fields.Many2one( 'simrp.state', 'State', required = True )
    distance = fields.Integer( 'Eway Distance', default=180 )
    
    porder_s = fields.One2many( 'simrp.porder', 'party_', 'Open Purchase Orders', domain=[('state', '=', 'o')] )
    subcondc_s = fields.One2many( 'simrp.subcondc', 'party_', 'Open Purchase Orders', domain=[('state', '=', 'o')] )

    category = fields.Selection( [
            ( 't', 'Regular Trade' ),
            ( 'i', 'Internal Group' ),
            ( 'o', 'Old Transactions' ),
            ( 'n', 'Non Credit / Suspense' ),
            ], 'Category', required=True, default='t' )

    dispmode = fields.Selection( [
            ( 'dc', 'DC1, DC2, .. >> Invoice' ),
            ( 'inv', 'DC1 + Single Item Invoice' ),
            ], 'Dispatch Mode', default='inv' )

    bankac = fields.Char( 'Bank A/c No. **', default='' )
    bankifsc = fields.Char( 'Bank IFSC **', default='' )
    bankacname = fields.Char( 'A/c Name. (If different)', default='' )
    bank = fields.Char( 'Bank / Branch', default='' )

    state = fields.Selection( [
            ( 'o', 'Open' ),
            ( 'l', 'Lock' )
            ], 'State', readonly = True, default='o' )

    bankphoto = fields.Binary( 'Bank Photo **', attachment=True )
    bankphotoname = fields.Char( 'Bank Photo Name' )

    def submit(self):
        if ( self.associate not in [ 'cust', 'bank' ] ):
            if ( not self.bankac ) or ( not self.bankifsc ) or ( not self.bankphoto ):
                raise exceptions.UserError('Bank A/c no OR IFSC OR photo is missing')
            if len( self.bankifsc ) != 11:
                raise exceptions.UserError('IFSC should be 11 characters')
        
        self.state = 'l'
        return True

    # def lock(self):
        # self.state = 'l'
        # return True

    def dummy( self ):
        return True
        
    def unlock(self):
        self.state = 'o'
        return True

    # @api.model
    # def getTdsRate( self ):
        # tdsrate = 0.01
        # if self.firmtype != 'i':
            # tdsrate = 0.02
        # if self.associate == 'p':
            # tdsrate = 0.10
        # return tdsrate

    @api.model
    def create(self, vals):
        o = super().create(vals)
        self.env[ 'simrp.auditlog' ].log( o, 'Create Party', {}, False )
        return o

    def write(self, vals):
        if 'state' not in vals:
            self.env[ 'simrp.auditlog' ].log( self, 'Change Party:', vals, False )
        return super().write(vals)


class State(models.Model):
    _name = 'simrp.state'
    
    name = fields.Char( 'State Name', size = 50, required = True )
    gstcode = fields.Char( 'GST State Code', size = 5, required = True )
    
    @api.model
    def gstname( self ):
        return self.gstcode + '-' + self.name
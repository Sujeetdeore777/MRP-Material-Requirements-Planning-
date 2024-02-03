import datetime
from odoo import api, fields, models, exceptions
from dateutil.relativedelta import relativedelta
from . import shiftinfo
from num2words import num2words
from urllib.parse import quote
import base64
import json
import re

import pytz


class Eway(models.Model):
    _name = 'simrp.eway'

    def ewayfile(self, o, oname, odistance, oamt ):
        c = self.env.user.company_id
        
        d = { 'version': "1.0.0219", 'billLists': [] }
        t = o.saleorder_.taxscheme_.compute( o.saleorder_.rate * o.okoutqty )
        e = { 
            'userGstin': c.company_registry, 
            'supplyType': 'O', 
            'subSupplyType': 1, 
            'docType': 'INV', 
            'docNo': oname, 
            'docDate': o.invdate.strftime('%d/%m/%Y'), 
            'transType': 1, 
            'fromGstin': c.company_registry, 
            'fromTrdName': c.name, 
            'fromAddr1': c.street, 
            'fromAddr2': c.street2, 
            'fromPlace': c.city, 
            'fromPincode': int( c.zip ), 
            'fromStateCode': int( c.state_id.code ), 
            'actualFromStateCode': int( c.state_id.code ), 
            'toGstin': o.party_.gstno, 
            'toTrdName': o.party_.name, 
            'toAddr1': o.party_.address1, 
            'toAddr2': ( o.party_.address2 if o.party_.address2 else '' ) + " " + ( o.party_.address3 if o.party_.address3 else '' ), 
            'toPlace': '', 
            'toPincode': int( o.party_.pincode ), 
            'toStateCode': int( o.party_.state_.gstcode ), 
            'actualToStateCode': int( o.party_.state_.gstcode ), 
            'totalValue': round( o.saleorder_.rate * o.okoutqty, 2 ), 
            'cgstValue': round( t[ 'taxclass' ][ 'cgst' ], 2 ), 
            'sgstValue': round( t[ 'taxclass' ][ 'sgst' ], 2 ), 
            'igstValue': round( t[ 'taxclass' ][ 'igst' ], 2 ), 
            'cessValue': 0.00, 
            'TotNonAdvolVal': 0.00, 
            'OthValue': 0.00, 
            'totInvValue': round( oamt, 2 ), 
            'transMode': 1, 
            'transDistance': odistance, 
            'transporterName': ( o.transportparty_.name if o.transportparty_ else '' ), 
            'transporterId': ( o.transportparty_.gstno if o.transportparty_ else '' ), 
            'transDocNo': '', 
            'transDocDate': '', 
            'vehicleNo': ( re.sub( "[^0-9a-zA-Z]+", "", o.vehicle ) if o.vehicle else '' ), 
            'vehicleType': 'R', 
            'mainHsnCode': int( o.saleorder_.itemrate_.item_.hsnsac ), 
            'itemList': [ {
                'itemNo': 1, 
                'productName': o.item_.dwg_no, 
                'productDesc': o.item_.des, 
                'hsnCode': int( o.saleorder_.itemrate_.item_.hsnsac ), 
                'quantity': round( o.okoutqty, 2 ), 
                'qtyUnit': o.item_.uom_.gstcode, 
                'taxableAmount': round( o.saleorder_.rate * o.okoutqty, 2 ), 
                'sgstRate': t[ 'taxclass' ][ 'sgstrate' ], 
                'cgstRate': t[ 'taxclass' ][ 'cgstrate' ], 
                'igstRate': t[ 'taxclass' ][ 'igstrate' ], 
                'cessRate': 0, 
                'cessNonAdvol': 0
                } ]
        }
        d[ 'billLists' ] = [ e ]
        return base64.b64encode( json.dumps( d ).encode("utf-8") )

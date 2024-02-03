# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, exceptions 
import logging
_logger = logging.getLogger(__name__)

class Taxscheme(models.Model):
    _name = 'simrp.taxscheme'
    
    name = fields.Char( 'Tax Scheme Name', size = 50, required = True )
    taxline_s = fields.One2many( 'simrp.taxline', 'taxscheme_', 'Taxline' )
    gstcheck = fields.Boolean( 'GST check', default=True, required = True )
    account_ = fields.Many2one( 'simrp.account', 'Basic Account 1' )
    account2_ = fields.Many2one( 'simrp.account', 'Basic Account 2' )
    share = fields.Float( 'Basic Account 2 Share', digits=(8,2), default=0 )

    def compute(self, basicAmount):
        """
        RETURN: {
                'tax': 0.0,                # Total taxes
                'printTaxes': []                  # List of taxes
            }
        """
        taxAmount = 0.0
        lastTaxAmount = 0.0
        subTotal = basicAmount
        ba1 = basicAmount
        ba2 = 0
        
        igst = 0
        sgst = 0
        cgst = 0
        igstrate = 0
        sgstrate = 0
        cgstrate = 0
        if self.share > 0:
            ba1 = basicAmount * ( 100 - self.share ) / 100
            ba2 = basicAmount * ( self.share ) / 100
        res = []
        for tl in self.taxline_s:
            if tl.on == 'basic':
                lastTaxAmount = (basicAmount * tl.rate / 100)
            if tl.on == 'basic1':
                lastTaxAmount = (ba1 * tl.rate / 100)
            if tl.on == 'basic2':
                lastTaxAmount = (ba2 * tl.rate / 100)
            elif tl.on == 'subtotal':
                lastTaxAmount = (subTotal * tl.rate)
            elif tl.on == 'lasttax':
                lastTaxAmount = (lastTaxAmount * tl.rate / 100)
            taxAmount += lastTaxAmount
            subTotal += lastTaxAmount
            if tl.taxclass == 'igst':
                igst = igst + lastTaxAmount
                igstrate = tl.rate
            if tl.taxclass == 'sgst':
                sgst = sgst + lastTaxAmount
                sgstrate = tl.rate
            if tl.taxclass == 'cgst':
                cgst = cgst + lastTaxAmount
                cgstrate = tl.rate
            res.append({
                        'name': tl.name,
                        'rate': tl.rate,
                        'taxamount': lastTaxAmount,
                        'taxclass': tl.taxclass,
                        'taxaccountid': tl.account_.id
            })
        #_logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " + str(taxAmount) )
        return {
                'tax': taxAmount,
                'printTaxes': res,
                'ba1': ba1,
                'ba2': ba2,
                'taxclass': { 'igst': igst, 'cgst': cgst, 'sgst': sgst, 
                                'igstrate': igstrate, 'cgstrate': cgstrate, 'sgstrate': sgstrate,
                                'totalrate': igstrate + cgstrate + sgstrate }
        }



class Taxline(models.Model):
    _name = 'simrp.taxline'
    
    name = fields.Char( 'Print Text', size = 50, required = True )
    sequence = fields.Integer( 'Sequence', required = True )
    rate = fields.Float( 'Rate', digits=(8,2), required = True )
    account_ = fields.Many2one( 'simrp.account', 'Tax Account', required = True )
    taxscheme_ = fields.Many2one( 'simrp.taxscheme', 'Taxscheme' )
    taxclass = fields.Selection([
            ('none', 'None'),
            ('sgst', 'SGST'),
            ('cgst', 'CGST'),
            ('igst', 'IGST'),
            ], 'GST Tax Class', required=True, default='none')
    on = fields.Selection([
            ('basic', 'Basic Amount'),
            ('basic1', 'Basic Amount 1 only'),
            ('basic2', 'Basic Amount 2 only'),
            ('subtotal', 'Current Subtotal'),
            ('lasttax', 'Last Tax Amount')
            ], 'On', required=True, default='b')
    _order = 'sequence'

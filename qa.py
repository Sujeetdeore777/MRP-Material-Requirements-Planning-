# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models

class ProcessQAP(models.Model):
    _name = 'simrp.processqap'
    _description = 'Process QAP'
    
    FREQ_LIST = [
        ('100', '100%: every pc'),
        ('20', '20%: every 5'),
        ('10', '10%: every 10'),
        ('4', '4%: every 25'),
        ('2', '2%: every 50'),
        ('1', '1%: every 100'),
        ('0.2', '0.2%: 500'),
        ('0.1', '0.1%: 1000'),
        ('r', '1st on reset'),
        ('fpa', 'FPA only'),
        ('aql', 'AQL Qty'),
        ]
        
    TYPE_LIST = [
        ('a', 'Attr.'),
        ('m', 'Meas.'),
        ('mspc', 'Meas. SPC'),
        ('asc', 'SC/CC Attr'),
        ('msc', 'SC/CC Meas'),
        ]
        
        
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Process', required=True)
    param = fields.Char('Parameter', required=True)
    type = fields.Selection(TYPE_LIST, 'Type', default='m', required=True)
    low = fields.Float('LL', digits=(8,4) )
    high = fields.Float('UL', digits=(8,4) )
    freq = fields.Selection(FREQ_LIST, 'Frequency', default='100', required=True)
    instrumentcategory_ = fields.Many2one('simrp.itemcategory', 'I.Cat', domain="[('type', 'in', ['instrument','equipment'])]")
    insrumentcode = fields.Many2one('simrp.item', 'Ins.', domain="[('type', 'in', ['equipment','instrument']), ('state', '=', 'a')]")
    pdir = fields.Boolean('PD', default=False)
    react = fields.Char('Reaction', required=True)

    _rec_name = 'param'

    def freqname(self):
        d = {}
        for li in self.FREQ_LIST:
            d[ li[ 0 ] ] = li[ 1 ]
        return d[ self.freq ]

    def typename(self):
        d = {}
        for li in self.TYPE_LIST:
            d[ li[ 0 ] ] = li[ 1 ]
        return d[ self.type ]

        
    # @api.multi
    # def name_get(self):
        # result = []
        # for o in self:
            # name = o.itemprocess_.item_.name + ' {' + o.itemprocess_.item_.name + '} ' + o.param
            # result.append( ( o.id, name ) )
        # return result
        
    @api.multi
    def getFrequencyNames( self ):
        return True
        #return self.FREQ_LIST - convert list to JSON and return as string

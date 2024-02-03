# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models

class AssetRedTag(models.Model):
    _name = 'simrp.assetredtag'
    _description = 'Rejection Record'
    
    code = fields.Char('Item Code', readonly=True)
    item_ = fields.Many2one('simrp.item', 'Asset Item', domain="[('type', 'in', ['equipment','instrument']), ('state', '=', 'a')]")
    problem = fields.Text('Problem', required=True)
    problemdatetime = fields.Datetime('Problem Date Time', default=datetime.date.today(), required=True)
    reportedby = fields.Char('Reported By')
    
    type = fields.Selection([
        ('mb', 'Machine Breakdown'),
        ('mv', 'Machine Visual Problem'),
        ('ml', 'Machine Leakage / Spillage'),
        ('a', 'Accuracy / Function'),
        ('n', 'Noise / vibration'),
        ('l', 'Loose parts'),
        ('d', 'Defective or Broken Part'),
        ('o', 'Other'),
        ], 'Type', default='mb', required=True)

    actionby = fields.Char('Correction by')
    actiondesc = fields.Text('List of work done')
    recordno = fields.Char('Service Record No / Agency')
    closedesc = fields.Text('Close / Status description')
    
    state = fields.Selection([
        ('o', 'Open'),
        ('m', 'Monitoring'),
        ('n', 'Not Solved'),
        ('s', 'Solved and closed')
        ], 'Type', default='o', readonly=True)
      
    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('simrp.redtag')
        return super(AssetRegTag, self).create(vals)
    @api.multi
    def monitor(self):
        self.update({'state':'m'})
        return True
    @api.multi
    def notsolved(self):
        self.update({'state':'ns'})
        return True
    @api.multi
    def solved(self):
        self.update({'state':'s'})
        return True

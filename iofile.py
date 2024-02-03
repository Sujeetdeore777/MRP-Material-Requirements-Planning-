import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class Iofile(models.Model):
    _name = 'simrp.iofile'
    
    name = fields.Char( 'File Code', size = 15, readonly = True )
    type = fields.Selection( [
            ( 'photo', 'Photo(jpeg, png, bmp)' ),
            ( 'doc', 'Document( pdf )' ),
            ], 'Type', required = True )
    item_ = fields.Many2one('simrp.item', 'Item')
    itemprocess_ = fields.Many2one('simrp.itemprocess', 'Itemprocess')
    store = fields.Binary( 'File', attachment=True, required = True )
    storename = fields.Char( 'Name' )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('siomin.iofile')
        return super(Iofile, self).create(vals)
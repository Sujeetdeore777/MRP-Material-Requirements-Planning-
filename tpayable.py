import datetime, time
import base64, json
import calendar
from odoo import api, fields, models, exceptions 
from odoo.tools import float_round
from num2words import num2words
import logging
_logger = logging.getLogger(__name__)

class TPayableReport(models.Model):
    _name = 'simrp.tpayable'
    
    date = fields.Date( 'Payment Cycle Date',default=lambda self: fields.Date.today(), required = True )
    tpayablerecords_s = fields.One2many( 'simrp.tpayablerecords', 'tpayable_', 'Regular Parties', domain=[('category','=','t')] )
    tpayablerecords_s_other = fields.One2many( 'simrp.tpayablerecords', 'tpayable_', 'Other Parties', domain=[('category','!=','t')] )
    tpayablerecords_s_all = fields.One2many( 'simrp.tpayablerecords', 'tpayable_', 'All Parties' )

    fundaccount_ = fields.Many2one( 'simrp.account', 'Fund Account', required = True)
    state = fields.Selection( [
            ( 'st', 'Start' ),
            ( 's', 'Selection' ),
            ( 'sub', 'Submit' ),
            ( 'd', 'Document Prep' ),
            ( 'u', 'Uploaded..' ),
            ( 'a', 'Approved' ),
            ( 'r', 'Recorded' )
            ], 'State', default='st', readonly = True )
    tpayabletreerecords_s = fields.One2many( 'simrp.tpayabletreerecords', 'tpayable_', 'Selected Bills', domain=[('check','=',True)])
    fundtransaction_s = fields.One2many( 'simrp.fundtransaction', 'tpayable_', 'Generated Transactions')

    bankfile = fields.Binary( 'Bank File' )
    bankfilename = fields.Char( 'Bank File Name' )

    _order = 'id desc'
    

    def deleterecord( self ):
        for tpr in self.tpayablerecords_s_all:
            for tprt in tpr.tpayabletreerecords_s:
                tprt.unlink()
            tpr.unlink()
        # for tpr in self.tpayablerecords_s_other:
            # for tprt in tpr.tpayabletreerecords_s:
                # tprt.unlink()
            # tpr.unlink()
        self.unlink()
        
    def update(self):
        return True

    def uploaded(self):
        self.state = 'u'
        return True
    def bankapprove(self):
        self.state = 'a'
        return True

    def approve( self ):
        pa = 0
        for tpr in self.tpayablerecords_s_all:
            pa = pa + tpr.balance
            if tpr.balance >= 0:
                for tprt in tpr.tpayabletreerecords_s:
                    tprt.sudo().unlink()
                tpr.sudo().unlink()
            else:
                for tprt in tpr.tpayabletreerecords_s:
                    tprt.lock = True
        self.state = 'd'
        self.env[ 'simrp.auditlog' ].log( self, 'Payment: ' + str( pa ), {}, False, False )        
        return True
        
    @api.multi
    def email(self):
        for rec in self:
            for r in rec.tpayablerecords_s_all:
                if r.balance < 0:
                    string = "\nTo,\n" + "   " + str(r.party_.account_.name )+ "\n" + "Dear Sir/Madam,\n" + "   Your payment is released now, please collect your cheque as soon as possible.\n" + "cheque amount " + str(abs(r.balance)) + "\n Payment Against:\n"
                    for d in r.tpayabletreerecords_s:
                        if d.check:
                            string = string + "\nAgst Ref :" + str(d.accline_.ref_.name) + "   " + str(d.doc_date) + "   " + str(abs(d.bal_amt)) + "   " + str(d.due_date) + "   " + "   " + str(d.due)
                    string = string + " \nTotal Amount : " + str(abs(r.balance)) + "\n\n Through:\n\n  HDFC Bank\n Cheque No: " + str(r.chq_no) + "\n Amount (in words): " + str(r.a2w())
                    _logger.info(string + "\n \n")
            return True

    @api.multi
    def printcheque(self):
        return self.env.ref('simrp.action_report_printcheque').report_action(self)

    def bankfilegen( self ):
        buc = self.env['ir.config_parameter'].sudo().get_param('bankuploadcode')
        if not buc:
            raise exceptions.UserError('System parameter "bankuploadcode" not set' )
        bf = ''
        for r in self.tpayablerecords_s_all:
            if ( r.party_.state != 'l' ) and ( r.chq_no != '' ):
                raise exceptions.UserError('Party record commercials not locked: ' + r.party_.name + '\nIn case of manual payment, enter transaction details before bank file generate' )
            acn = r.party_.bankacname if r.party_.bankacname else r.party_.name
            bf = bf + 'N,,' + r.party_.bankac + ',' + "{:.2f}".format(abs(r.balance)) + ',' + acn
            bf = bf + ',,,,,,,,' + self.env.user.company_id.name + ',' + acn[:20] + ',,,,,,,,,' + fields.date.today().strftime("%d/%m/%Y")
            bf = bf + ',,' + r.party_.bankifsc + ',,,' + '\n'
        _logger.info( bf )
        self.bankfile = base64.b64encode( bf.encode('utf-8') )
        self.bankfilename = buc + "_bank_" + self.env.user.company_id.name + "_" + fields.Datetime.now().strftime("%m%d%Y%H%M%S") + ".csv"
        return True

    def loadparty( self, p ):
        acclines = self.env['simrp.accline'].search( [ ( 'account_', '=', p.account_.id ) ], order='docdate' )

        billsupto = self.date - datetime.timedelta( days=p.creditperiod )

        netledger = 0
        netdueamt = 0
        unadjdramt = 0
        for d in acclines:
            netledger = netledger + d.amountdr - d.amountcr
            if d.baladjAmount != 0:
                unadjdramt = unadjdramt + d.baladjAmount
            if d.docdate <= billsupto:
                netdueamt = netdueamt + d.baladjAmount

        purchases = self.env[ 'simrp.purchase' ].search( [ ( 'party_','=',p.id ), ( 'gstr2state','in',['n','x'] ), ( 'state', '=', 'a' ) ] )
        gstr2mm = 0
        for pur in purchases:
            gstr2mm = gstr2mm + pur.taxamount
                
        if ( (netledger < -5) and ( netdueamt < -5 ) ):                    # payable more than threshold
            tpr = self.env[ 'simrp.tpayablerecords' ].create( {
                'tpayable_': self.id,
                'party_': p.id,
                'credit': p.creditperiod,
                'due_upto': billsupto,
                'due_amt': netdueamt,
                'net_ledger': netledger,
                'unadj_dr': unadjdramt,
                'gstr2mm': gstr2mm,
                'date': self.date,
            } )
        
            for d in acclines:
                due = ''
                if d.docdate <= billsupto:
                    due = "due"
                if d.baladjAmount != 0:
                    transaction = " "
                    if d.ref_:
                        transaction = d.ref_.name
                    due_date = d.docdate + datetime.timedelta(days=p.creditperiod)
                    line = self.env[ 'simrp.tpayabletreerecords' ].create( {
                        'tpayablerecords_': tpr.id,
                        'tpayable_': self.id,
                        'accline_': d.id,
                        'tran': transaction,
                        'due_date': due_date,
                        'due': due,
                    } )

    def generates(self):
        self.state = 's'
        for rec in self:
            parties = self.env['simrp.party'].search( [], order='name' )
            cnt = 0
            payt = 0
            duet = 0
            for p in parties:
                self.loadparty( p )
        return True

    def deleteparty( self, tprid ):
        for tpr in self.tpayablerecords_s_all:
            if tpr.id == tprid:
                for tprt in tpr.tpayabletreerecords_s:
                    tprt.sudo().unlink()
                tpr.sudo().unlink()

    def confirm(self):
        for r in self.tpayablerecords_s_all:
            if r.balance < 0:
                if not r.chq_no:
                    raise exceptions.UserError('Enter Cheque / Transfer No for all transactions')
    
        for r in self.tpayablerecords_s_all:
            if r.balance < 0:
                des = '[' + str( self.id ) + '] ' + r.party_.name + '-' + r.chq_no
                line = self.env[ 'simrp.fundtransaction' ].create( {
                    'ftdate': fields.Date.today().strftime( '%Y-%m-%d' ),
                    'tpayable_': self.id,
                    'fundaccount_': self.fundaccount_.id,
                    'party_': r.party_.account_.id,
                    'amount': abs(r.balance),
                    'des': des,
                } )
                line.submit()
                for d in r.tpayabletreerecords_s:
                    if d.check:
                        line1 = self.env[ 'simrp.refadj' ].create( {
                            'accline_': line.fundaccline_.id,
                            'agstaccline_': d.accline_.id,
                            'adjAmount': d.select_amt,
                        } )
        self.state = 'r'
        return True


class TPayabletable(models.Model):
    _name = 'simrp.tpayablerecords'
    
    tpayable_ = fields.Many2one( 'simrp.tpayable', 'tpayable', required=False)
    parentstate = fields.Selection( related='tpayable_.state' )
    party_ = fields.Many2one( 'simrp.party', 'Party',readonly = True)
    partystate = fields.Selection( related='party_.state' )
    
    category = fields.Selection( related='party_.category' )

    credit = fields.Integer( 'Credit',readonly = True)
    due_upto = fields.Date( 'Due Upto',readonly = True )
    due_amt = fields.Float( 'Due Bills',readonly = True )
    net_ledger = fields.Float( 'Net Ledger',readonly = True )
    unadj_dr = fields.Float( 'Unadj. Dr',readonly = True )
    date = fields.Date( related='tpayable_.date' )
    tpayabletreerecords_s = fields.One2many( 'simrp.tpayabletreerecords', 'tpayablerecords_', 'All Records', readonly=True)
    balance = fields.Float( 'Selected Amt.', digits=(8,2), compute='_amt')
    chq_no = fields.Char( 'Chq / Txn No.')

    gstr2mm = fields.Float( 'GSTR2!', readonly = True )
    
    adjproblem = fields.Boolean( 'Adjproblem', compute='_adjproblem' )
    def _adjproblem( self ):
        for o in self:
            r = True
            if abs( o.unadj_dr - o.net_ledger ) > 1:
                r = False
                _logger.info( 'ADJJJJ ' + str( o.unadj_dr ) + ' ' + str( o.net_ledger ) )
            o.adjproblem = r

    def dummy( self ):
        return True
        
    # @api.model
    # def create(self, vals):
        # c = super(TPayabletable, self).create(vals)
        # c.update()

    # @api.multi
    # def update(self):
        # for rec in self:
                # return True

    def unlink( self ):
        for o in self:
            for tptr in o.tpayabletreerecords_s:
                tptr.unlink()
        return super().unlink()
        
    def reload( self ):
        p = self.party_
        tp = self.tpayable_
        self.tpayable_.deleteparty( self.id )
        tp.loadparty( p )

    @api.multi
    def _amt(self):
        for o in self:
            amt = 0
            for r in o.tpayabletreerecords_s:
                if r.check:
                    amt = amt + (r.select_amt)
            o.balance = amt

    @api.model
    def a2w( self ):
        return num2words( abs(self.balance) )

class TPayableTreetable(models.Model):
    _name = 'simrp.tpayabletreerecords'
    
    tpayablerecords_ = fields.Many2one( 'simrp.tpayablerecords', 'tpayablerecords', required=False)
    tpayable_ = fields.Many2one( 'simrp.tpayable', 'tpayable', required=False)

    accline_ = fields.Many2one( 'simrp.accline', 'Accline',readonly = True)
    pname = fields.Char( related='accline_.account_.name' )
    tran = fields.Char( 'Trasaction',readonly = True )
    doc_date = fields.Date( related='accline_.docdate' )
    doc_dr = fields.Float(related='accline_.amountdr')
    doc_cr = fields.Float(related='accline_.amountcr')
    bal_amt = fields.Float( related='accline_.baladjAmount' )
    due_date = fields.Date( 'Due Date',readonly = True )
    due = fields.Char( 'Due',readonly = True )
    check = fields.Boolean( '+', default=False, readonly=True)
    select_amt = fields.Float( 'Selected Amt.', digits=(8,2),readonly = True)

    lock = fields.Boolean(default=False, readonly=True)

    _order = "id"

    @api.multi
    def checkboxstatus(self):
        if self.check:
            self.check = False
            self.select_amt = 0
        else:
            self.check = True
            self.select_amt = self.bal_amt
        return True

class Adhocbank(models.Model):
    _name = 'simrp.adhocbank'
    
    date = fields.Date( 'Date',default=lambda self: fields.Date.today(), readonly = True )
    party_ = fields.Many2one( 'simrp.party', 'Party', required = True )
    reason = fields.Char( 'Reason', size = 200, required = True )
    amount = fields.Float( 'Amount', digits=(8,2), required = True ) 

    bankfile = fields.Binary( 'Bank File', readonly = True )
    bankfilename = fields.Char( 'Bank File Name' )

    state = fields.Selection( [
            ( 'n', 'New' ),
            ( 'g', 'Generated' ),
            ( 'd', 'Done' ),
            ], 'State',default='n', readonly = True )
            
    _order = 'id desc'

    def bankfilegen( self ):
        buc = self.env['ir.config_parameter'].sudo().get_param('bankuploadcode')
        if not buc:
            raise exceptions.UserError('System parameter "bankuploadcode" not set' )
        bf = ''
        r = self
        if ( r.party_.state != 'l' ):
            raise exceptions.UserError('Party record commercials not locked: ' + r.party_.name + '\nIn case of manual payment, enter transaction details before bank file generate' )
        acn = r.party_.bankacname if r.party_.bankacname else r.party_.name
        bf = bf + 'N,,' + r.party_.bankac + ',' + "{:.2f}".format(abs(r.amount)) + ',' + acn
        bf = bf + ',,,,,,,,' + self.env.user.company_id.name + ',' + acn[:20] + ',,,,,,,,,' + fields.date.today().strftime("%d/%m/%Y")
        bf = bf + ',,' + r.party_.bankifsc + ',,,' + '\n'
        _logger.info( bf )
        self.bankfile = base64.b64encode( bf.encode('utf-8') )
        self.bankfilename = buc + "_bank_" + self.env.user.company_id.name + "_" + fields.Datetime.now().strftime("%m%d%Y%H%M%S") + ".csv"
        self.state = 'g'
        return True

    def done( self ):
        self.bankfile = False
        self.bankfilename = False
        self.state = 'd'

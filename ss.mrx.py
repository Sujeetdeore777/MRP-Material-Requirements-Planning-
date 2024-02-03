items = self.env[ 'simrp.item' ].search( [ ('active','=',True), ( 'state', '=', 'a' ) ], order='type, category' )
fromdt = datetime.datetime(self.fromdate.year, self.fromdate.month, self.fromdate.day)
todt = datetime.datetime(self.todate.year, self.todate.month, self.todate.day)
for i in items:
    _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<SS: " + str( i.id ) )
    ios = self.env[ 'simrp.openingstock' ].search( [ ('item_','=',i.id) ] )
    oprate = 0
    if len( ios ) > 0:
        oprate = ios[ 0 ].rate
    istocks = self.env[ 'simrp.stock' ].search( [ ('item_','=',i.id), ('recdate', '<=', todt) ], order='recdate' )
    ss_opstock = 0
    ss_pogrnq = 0
    ss_subcongrnq = 0
    ss_subcondcq = 0
    ss_subconstockq = 0
    ss_sjournalq = 0
    ss_womfgq = 0
    ss_dispatchq = 0
    ss_debitq = 0
    ss_physicalstockq = 0
    for ise in istocks:
        if self.type == 'ss':
            mov = ise.okinqty - ise.okoutqty
        else:
            mov = ise.rejinqty - ise.rejoutqty
        
        if ise.recdate < fromdt:
            #openstock calc
            ss_opstock = ss_opstock + mov
        else:
            #transaction stock calc
            #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<ref: " + ise.ref._name )
            isetype = ise.ref._name
            if isetype == 'simrp.grn':
                if ise.ref.subcondc_:
                    ss_subcondcq = ss_subcondcq + mov
                elif ise.ref.porder_:
                    ss_pogrnq = ss_pogrnq + mov
                else:
                    raise exceptions.UserError('Un identified GRN Type in stock entry:' + str( ise.id ) )
            elif isetype == 'simrp.dispatch':
                ss_dispatchq = ss_dispatchq + mov
            elif isetype == 'simrp.subcondc':
                ss_subcondcq = ss_subcondcq + mov
            elif isetype == 'simrp.debit':
                ss_dispatchq = ss_dispatchq + mov
            elif isetype == 'simrp.sjournal':
                ss_sjournalq = ss_sjournalq + mov
            elif isetype == 'simrp.physicalstock':
                ss_physicalstockq = ss_physicalstockq + mov
            elif isetype == 'simrp.womfg':
                ss_womfgq = ss_womfgq + mov
    
    isubcondcs = self.env[ 'simrp.subcondc' ].search( 
        [ ('item_','=',i.id), ('recdate', '<=', todt), ( 'state', '=', 'o' ) ] )
    for isdc in isubcondcs:
        ss_subconstockq = ss_subconstockq + isdc.balanceqtyi

    ss_closingstock = ss_opstock + ss_pogrnq + ss_subcongrnq + ss_subcondcq + ss_subconstockq + ss_sjournalq + ss_womfgq + ss_dispatchq + ss_debitq + ss_physicalstockq

    ss_clrate = oprate
    if i.type in ['fg','scrap']:
        r = self.env[ 'simrp.itemrate' ].search( [ ('item_','=',i.id) ], order='rate' )
        if len( r ) > 0:
            ss_clrate = r[ 0 ].rate
    else:
        r = self.env[ 'simrp.porder' ].search( [ ('item_','=',i.id) ], limit=1, order='podate desc' )
        if len( r ) > 0:
            ss_clrate = r[ 0 ].rate

    self.env[ 'simrp.reportdetails' ].create( {
        'reportm_': self.id,
        'ss_item': i.name,
        'ss_itemtype': i.type,
        'ss_itemcat': i.category.name,
        'ss_oprate': oprate,
        'ss_opval': ss_opstock * oprate,
        'ss_opstock': ss_opstock,
        'ss_itemuom': i.uom_.name,
        'ss_pogrnq': ss_pogrnq,
        'ss_subcongrnq': ss_subcongrnq,
        'ss_subcondcq': ss_subcondcq,
        'ss_subconstockq': ss_subconstockq,
        'ss_sjournalq': ss_sjournalq,
        'ss_womfgq': ss_womfgq,
        'ss_dispatchq': ss_dispatchq,
        'ss_debitq': ss_debitq,
        'ss_physicalstockq': ss_physicalstockq,
        'ss_closingstock': ss_closingstock,
        'ss_clrate': ss_clrate,
        'ss_clvalue': ss_closingstock * ss_clrate,
    } )


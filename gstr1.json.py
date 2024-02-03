o = self

r = {}
r[ "gstin" ] = self.env.user.company_id.company_registry
r[ "fp" ] = o.todate.strftime( '%m%Y' )
r[ "version" ] = "GST3.0.3"
r[ "hash" ] = "hash"

b2b = []
dr = o.env['simrp.dispatch'].search( [ ( 'invdate','>=',o.fromdate ), ( 'invdate','<=',o.todate ), ( 'state','=','i' ) ] )
for d in dr:
    bval = round( d.saleorder_.rate * d.okoutqty, 2 )
    dtax = d.saleorder_.taxscheme_.compute( bval )

    igst = round2( dtax[ 'taxclass' ][ 'igst' ], 2 )
    sgst = round2( dtax[ 'taxclass' ][ 'sgst' ], 2 )
    cgst = round2( dtax[ 'taxclass' ][ 'cgst' ], 2 )
    ival = round2( bval + igst + sgst + cgst, 2 )

    i = {}
    i[ "inum" ] = d.invno
    i[ "idt" ] = d.invdate.strftime( '%d-%m-%Y' )
    i[ "val" ] = ival
    i[ "pos" ] = d.party_.state_.gstcode
    i[ "rchrg" ] = "N"
    i[ "inv_typ" ] = "R"
    i[ "itms" ] = [	{ "num": int( str( int(dtax[ 'taxclass' ][ 'totalrate' ]) ) + '01' ), "itm_det": { 
                        "txval": bval, "rt": dtax[ 'taxclass' ][ 'totalrate' ], "camt": cgst, "samt": sgst, "iamt": igst, "csamt": 0
						}
				} ]
    
    b2b.append( { "ctin": d.party_.gstno, "inv": [ i ] } )
    
    # hsncode = d.item_.hsnsac
    # if hsncode not in hsnd.keys():
        # hsnd[ hsncode ] = { 'uqc': d.item_.uom_.gstr1code, 'tq': 0, 'tv': 0, 'bv': 0, 'igst': 0, 'cgst': 0, 'sgst': 0 }
        
    # hsnd[ hsncode ][ 'tq' ] = hsnd[ hsncode ][ 'tq' ] + d.okoutqty
    # hsnd[ hsncode ][ 'tv' ] = hsnd[ hsncode ][ 'tv' ] + round( d.invamt, 2 )
    # hsnd[ hsncode ][ 'bv' ] = hsnd[ hsncode ][ 'bv' ] + bval
    # hsnd[ hsncode ][ 'igst' ] = hsnd[ hsncode ][ 'igst' ] + 
    # hsnd[ hsncode ][ 'cgst' ] = hsnd[ hsncode ][ 'cgst' ] + dtax[ 'taxclass' ][ 'cgst' ]
    # hsnd[ hsncode ][ 'sgst' ] = hsnd[ hsncode ][ 'sgst' ] + dtax[ 'taxclass' ][ 'sgst' ]
r[ "b2b" ] = b2b

cdnr = []
dr = o.env['simrp.debit'].search( [ ( 'rdate','>=',o.fromdate ), ( 'rdate','<=',o.todate ), ( 'state','!=','p' ), ( 'gstreturn','=','1' ) ] )
for d in dr:
    bval = round( d.basicamount, 2 )
    dtax = d.taxscheme_.compute( bval )

    igst = round2( dtax[ 'taxclass' ][ 'igst' ], 2 )
    sgst = round2( dtax[ 'taxclass' ][ 'sgst' ], 2 )
    cgst = round2( dtax[ 'taxclass' ][ 'cgst' ], 2 )
    ival = round2( bval + igst + sgst + cgst, 2 )

    i = {}
    i[ "nt_num" ] = d.name
    i[ "nt_dt" ] = d.rdate.strftime( '%d-%m-%Y' )
    i[ "ntty" ] = "D"
    i[ "val" ] = ival
    i[ "pos" ] = d.party_.state_.gstcode
    i[ "rchrg" ] = "N"
    i[ "itms" ] = [	{ "num": int( str( int(dtax[ 'taxclass' ][ 'totalrate' ]) ) + '01' ), "itm_det": { 
                        "txval": bval, "rt": dtax[ 'taxclass' ][ 'totalrate' ], "camt": cgst, "samt": sgst, "iamt": igst, "csamt": 0
						}
				} ]
    cdnr.append( { "ctin": d.party_.gstno, "nt": [ i ] } )

dr = o.env['simrp.credit'].search( [ ( 'cndate','>=',o.fromdate ), ( 'cndate','<=',o.todate ), ( 'state','!=','p' ), ( 'gstreturn','=','1' ) ] )
for d in dr:
    bval = round( d.basicamount, 2 )
    dtax = d.taxscheme_.compute( bval )

    igst = round2( dtax[ 'taxclass' ][ 'igst' ], 2 )
    sgst = round2( dtax[ 'taxclass' ][ 'sgst' ], 2 )
    cgst = round2( dtax[ 'taxclass' ][ 'cgst' ], 2 )
    ival = round2( bval + igst + sgst + cgst, 2 )

    i = {}
    i[ "nt_num" ] = d.name
    i[ "nt_dt" ] = d.cndate.strftime( '%d-%m-%Y' )
    i[ "ntty" ] = "C"
    i[ "val" ] = ival
    i[ "pos" ] = d.party_.state_.gstcode
    i[ "rchrg" ] = "N"
    i[ "itms" ] = [	{ "num": int( str( int(dtax[ 'taxclass' ][ 'totalrate' ]) ) + '01' ), "itm_det": { 
                        "txval": bval, "rt": dtax[ 'taxclass' ][ 'totalrate' ], "camt": cgst, "samt": sgst, "iamt": igst, "csamt": 0
						}
				} ]
    cdnr.append( { "ctin": d.party_.gstno, "nt": [ i ] } )


r[ "cdnr" ] = cdnr

r1 = json.dumps( r )
n = "GSTR1_" + self.env.user.company_id.company_registry + "_" + o.todate.strftime( '%m%Y' ) + ".json"

#_logger.info(  )
self.json = base64.b64encode( r1.encode('utf-8') )
self.storename = n

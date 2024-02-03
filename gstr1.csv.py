s = ""
round2=lambda x,y=None: round(x + 0.0000000001,y)


o = self

dr = o.env['simrp.invoice'].search( [ ( 'invdate','>=',o.fromdate ), ( 'invdate','<=',o.todate ), ( 'state','=','i' ) ] )
s = 'Import B2B Section\n\n'
b = "GSTIN/UIN of Recipient,Receiver Name,Invoice Number,Invoice date,Invoice Value,Place Of Supply,Reverse Charge,Invoice Type,E-Commerce GSTIN,Rate,Applicable % of Tax Rate,Taxable Value,Cess Amount\n"

hsnd = {}
for d in dr:
    # bval = round2( d.saleorder_.rate * d.okoutqty, 2 )
    bval = d.basicamt
    dtax = d.saleorder_.taxscheme_.compute( bval )
    b = b + d.party_.gstno + ',' + d.party_.name + ','
    b = b + d.name + ',' + d.invdate.strftime( '%d-%b-%y' ) + ',' + str( d.invamt ) + ','
    b = b + d.party_.state_.gstname() + ',N,Regular,,'
    b = b + str( dtax[ 'taxclass' ][ 'totalrate' ] ) + ',,' + str( bval ) + ',\n'

    for disp in d.dispatch_s:
        hsncode = disp.item_.hsnsac
        if hsncode not in hsnd.keys():
            hsnd[ hsncode ] = { 'uqc': disp.item_.uom_.gstr1code, 'tq': 0, 'tv': 0, 'bv': 0, 'igst': 0, 'cgst': 0, 'sgst': 0, 'rate': 0 }

        dispbasic = disp.okoutqty * disp.rate
        disptax = d.saleorder_.taxscheme_.compute( dispbasic )
            
        hsnd[ hsncode ][ 'rate' ] = disptax[ 'taxclass' ][ 'totalrate' ]
        hsnd[ hsncode ][ 'tq' ] = hsnd[ hsncode ][ 'tq' ] + disp.okoutqty
        hsnd[ hsncode ][ 'tv' ] = hsnd[ hsncode ][ 'tv' ] + round2( disptax[ 'tax' ] + dispbasic, 2 )
        hsnd[ hsncode ][ 'bv' ] = hsnd[ hsncode ][ 'bv' ] + dispbasic
        hsnd[ hsncode ][ 'igst' ] = hsnd[ hsncode ][ 'igst' ] + disptax[ 'taxclass' ][ 'igst' ]
        hsnd[ hsncode ][ 'cgst' ] = hsnd[ hsncode ][ 'cgst' ] + disptax[ 'taxclass' ][ 'cgst' ]
        hsnd[ hsncode ][ 'sgst' ] = hsnd[ hsncode ][ 'sgst' ] + disptax[ 'taxclass' ][ 'sgst' ]

self.json = base64.b64encode( b.encode('utf-8') )
self.storename = "got_b2b_" + self.env.user.company_id.company_registry + "_" + o.todate.strftime( '%m%Y' ) + ".csv"
s = s + b

s = s + '\n\nImport HSN Section\n\n'
b = 'HSN,Description,UQC,Total Quantity,Total Value,Taxable Value,Integrated Tax Amount,Central Tax Amount,State/UT Tax Amount,Cess Amount,Rate\n'

for h in hsnd.keys():
    if h:
        b = b + h + ',,'
        b = b + hsnd[ h ][ 'uqc' ] + ',' + str( round2( hsnd[ h ][ 'tq' ], 2 ) ) + ',' + str( round2( hsnd[ h ][ 'tv' ], 2 ) )
        b = b + ',' + str( round2( hsnd[ h ][ 'bv' ], 2 ) ) + ',' + str( round2( hsnd[ h ][ 'igst' ], 2 ) ) + ',' + str( round2( hsnd[ h ][ 'cgst' ], 2 ) ) + ',' + str( round2( hsnd[ h ][ 'sgst' ], 2 ) ) + ',,' + str( round2( hsnd[ h ][ 'rate' ], 2 ) ) + '\n'

self.json1 = base64.b64encode( b.encode('utf-8') )
self.storename1 = "got_hsn_" + self.env.user.company_id.company_registry + "_" + o.todate.strftime( '%m%Y' ) + ".csv"
s = s + b

s = s + '\n\nImport CDNR Section\n\n'
b = 'GSTIN/UIN of Recipient,Receiver Name,Note Number,Note Date,Note Type,Place Of Supply,Reverse Charge,Note Supply Type,Note Value,Applicable % of Tax Rate,Rate,Taxable Value,Cess Amount\n'

dr = o.env['simrp.debit'].search( [ ( 'rdate','>=',o.fromdate ), ( 'rdate','<=',o.todate ), ( 'state','!=','p' ), ( 'gstreturn','=','1' ) ] )
for d in dr:
    bval = round2( d.basicamount, 2 )
    dtax = d.taxscheme_.compute( bval )

    taxamt = round2( dtax[ 'tax' ], 2 )
    ival = round2( bval + taxamt, 2 )

    b = b + d.party_.gstno + ',' + d.party_.name + ','
    b = b + d.name + ',' + d.rdate.strftime( '%d-%b-%y' ) + ',D,' + d.party_.state_.gstname() + ',N,Regular,' + str( ival ) + ',,'
    b = b + str( dtax[ 'taxclass' ][ 'totalrate' ] ) + ',' + str( bval ) + ',\n'

dr = o.env['simrp.credit'].search( [ ( 'cndate','>=',o.fromdate ), ( 'cndate','<=',o.todate ), ( 'state','!=','p' ), ( 'gstreturn','=','1' ) ] )
for d in dr:
    bval = round( d.basicamount, 2 )
    dtax = d.taxscheme_.compute( bval )

    taxamt = round2( dtax[ 'tax' ], 2 )
    ival = round2( bval + taxamt, 2 )

    b = b + d.party_.gstno + ',' + d.party_.name + ','
    b = b + d.name + ',' + d.cndate.strftime( '%d-%b-%y' ) + ',C,' + d.party_.state_.gstname() + ',N,Regular,' + str( ival ) + ',,'
    b = b + str( dtax[ 'taxclass' ][ 'totalrate' ] ) + ',' + str( bval ) + ',\n'

self.json2 = base64.b64encode( b.encode('utf-8') )
self.storename2 = "got_cdnr_" + self.env.user.company_id.company_registry + "_" + o.todate.strftime( '%m%Y' ) + ".csv"
s = s + b

s = s + '\n\nImport Docs Section\n\n'
s = s + '\n\nExport Section\n\n'
s = s + 'Pending\n'
                
self.csv = s

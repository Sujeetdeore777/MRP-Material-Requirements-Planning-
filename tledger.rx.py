df = workbook.add_format({'num_format': 'dd/mm/yy', 'border':1  })
nf = workbook.add_format({'num_format': '0.00', 'border':1 })
nfi = workbook.add_format({'num_format': '0', 'border':1 })
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'green', 'border':1 })
bd = workbook.add_format({'bold': True, 'align': 'right', 'border':1 })

bhead = workbook.add_format({'bold': True, 'bg_color': '#B2BABB', 'border':1 })
lg = workbook.add_format({'bg_color': '#D5D8DC', 'border':1 })

boldra = workbook.add_format({'bold': True, 'bg_color': 'yellow', 'align': 'right', 'border':1 })
nfg = workbook.add_format({'num_format': '0.00', 'bg_color': '#C8E6C9', 'border':1 })
nfr = workbook.add_format({'num_format': '0.00', 'bg_color': '#FFCDD2', 'border':1 })
nfgray = workbook.add_format({'num_format': '0.00', 'bg_color': '#DCD5D4', 'border':1 })
mergehead = workbook.add_format({ 'align': 'center', 'valign': 'vcenter', 'fg_color': '#000000', 'color': '#FFFFFF' , 'border':1 })
bheadsmall = workbook.add_format({ 'align': 'center', 'valign': 'vcenter', 'fg_color': '#B2BABB', 'border':1, 'font_size': 8 })
border = workbook.add_format({ 'border':1 })
smallb = workbook.add_format({ 'border':1, 'font_size': 8 })
merge = workbook.add_format({ 'align': 'center', 'valign': 'vcenter', 'border':1  })
mergedf = workbook.add_format({ 'align': 'center', 'valign': 'vcenter', 'num_format': 'dd/mm/yy', 'border':1 })    
sheet = workbook.add_worksheet( "Monthly Summary" )

co = self.env.user.company_id
sheet.write(0, 0, co.name, bhead)
sheet.write(1, 0, co.street, bhead)
sheet.write(2, 0, co.street2 + ", " + co.city + " - " + co.zip, bhead)

# sheet.write(0, 1, "Monthly Summary", boldra)
sheet.merge_range('B1:G1', 'Monthly Summary', mergehead)
sheet.write(1, 1, "Party:", lg)
sheet.merge_range('C2:G2', o.account_.name, merge)
# sheet.write(1, 2, o.account_.name)
sheet.write(2, 1, "Period:", lg)
sheet.merge_range('C3:D3', o.sdate, mergedf)
# sheet.write(2, 2, o.sdate, df)
sheet.write(2, 4, "to", lg)
sheet.merge_range('F3:G3', o.edate, mergedf)
# sheet.write(2, 5, o.edate, df)


sheet.write(3, 0, "Period", lg)
sheet.write(3, 1, "", lg)
sheet.write(3, 2, "Dr. Amount", lg)
sheet.write(3, 3, "Cr. Amount", lg)
sheet.write(3, 4, "", lg)
sheet.write(3, 5, "Cumulative", lg)
sheet.write(3, 6, "", lg)

for i in range( 0, 7 ):
    sheet.write( 4, i, "", border )

sheet.set_column( 0, 0, 35 )
sheet.set_column( 2, 3, 10 )
sheet.set_column( 4, 4, 3.25 )
sheet.set_column( 5, 5, 10 )
sheet.set_column( 6, 6, 3.25 )

# border_format=workbook.add_format({ 'border':1 })
# sheet.conditional_format( 'A1:D12' , { 'type' : 'blanks' , 'format' : border_format} )

dtot = 0
ctot = 0

cu = 0
def pa( des, a, cu, r, dr=0, cr=0 ):
    global sheet, nf, border, dtot, ctot
    sheet.write(r, 0, des, border)
    sheet.write(r, 1, "", border)
    sheet.write(r, 4, "", border)
    if cu < 0:
        sheet.write(r, 5, -cu, nf)
        sheet.write(r, 6, "Cr", border)
    if cu >= 0:
        sheet.write(r, 5, cu, nf)
        sheet.write(r, 6, "Dr", border)
    sheet.write(r, 2, "", border)
    sheet.write(r, 3, "", border)
    if a < 0:
        sheet.write(r, 3, -a, nf)
        ctot = ctot - a
    if a > 0:
        sheet.write(r, 2, a, nf)
        dtot = dtot + a
    if a == 0:
        if dr > 0:
            sheet.write(r, 2, dr, nf)
            dtot = dtot + dr
        if cr > 0:
            ctot = ctot + cr
            sheet.write(r, 3, cr, nf)
    # if ba != 0:
        # sheet.write(r, 8, ba, nf)
    
cu = o.opbalance
pa( "Opening Balance", cu, cu, 5 )

monthlist = [dt.strftime("%b-%y") for dt in rrule(MONTHLY, dtstart=o.sdate, until=o.edate)]

mdict = {}
for m in monthlist:
    mdict[ m ] = { 'dr': 0, 'cr': 0 }

for tal in o.taccline_s:
    if tal.docdesc != 'Opening balance':
        docmonth = tal.docdate.strftime("%b-%y")
        mdict[ docmonth ][ 'dr' ] = mdict[ docmonth ][ 'dr' ] + tal.amountdr
        mdict[ docmonth ][ 'cr' ] = mdict[ docmonth ][ 'cr' ] + tal.amountcr
        # mdict[ docmonth ][ 'ba' ] = mdict[ docmonth ][ 'ba' ] + tal.baladjAmount
    
r = 6

for m in monthlist:
    cu = cu + mdict[ m ][ 'dr' ] - mdict[ m ][ 'cr' ]
    pa( m, 0, cu, r, mdict[ m ][ 'dr' ], mdict[ m ][ 'cr' ] )
    r = r + 1

sheet.write(r, 0, "Total", mergehead)
sheet.write(r, 1, "", nft)
sheet.write(r, 2, dtot, nft )
sheet.write(r, 3, ctot, nft )
sheet.write(r, 4, "", nft)
sheet.write(r, 5, cu, nft)
sheet.write(r, 6, "", nft)








sheet = workbook.add_worksheet( "Ledger Statement" )

sheet.merge_range('A1:B1', co.name, bheadsmall)
sheet.merge_range('A2:B2', co.street, bheadsmall)
sheet.merge_range('A3:B3', co.street2 + ", " + co.city + " - " + co.zip, bheadsmall)

sheet.merge_range('C1:F1', 'Ledger Statement', mergehead)
sheet.merge_range('C2:F2', o.account_.name, merge)
sheet.merge_range('C3:F3', o.sdate.strftime("%d.%b.%y") + " to " + o.edate.strftime("%d.%b.%y"), merge)

sheet.write(3, 0, "Date", lg)
sheet.write(3, 1, "Document", lg)
sheet.write(3, 2, "Description", lg)
sheet.write(3, 3, "Dr. Amount", lg)
sheet.write(3, 4, "Cr. Amount", lg)
sheet.write(3, 5, "", lg)

for i in range( 0, 6 ):
    sheet.write( 4, i, "", border )

sheet.set_column( 0, 0, 9.09 )
sheet.set_column( 1, 1, 13.91 )
sheet.set_column( 2, 2, 42.45 )
sheet.set_column( 3, 4, 9.91 )
sheet.set_column( 5, 5, 0.56 )




sheetb = workbook.add_worksheet( "Bills Summary" )

sheetb.merge_range('A1:B1', co.name, bheadsmall)
sheetb.merge_range('A2:B2', co.street, bheadsmall)
sheetb.merge_range('A3:B3', co.street2 + ", " + co.city + " - " + co.zip, bheadsmall)

sheetb.merge_range('C1:F1', 'Bills Summary', mergehead)
sheetb.merge_range('C2:F2', o.account_.name, merge)
sheetb.merge_range('C3:F3', o.sdate.strftime("%d.%b.%y") + " to " + o.edate.strftime("%d.%b.%y"), merge)

sheetb.write(3, 0, "Date", lg)
sheetb.write(3, 1, "Document", lg)
sheetb.write(3, 2, "Dr. Amount", lg)
sheetb.write(3, 3, "Cr. Amount", lg)
sheetb.write(3, 4, "", lg)
sheetb.write(3, 5, "Balance Adj", lg)

for i in range( 0, 6 ):
    sheetb.write( 4, i, "", border )

sheetb.set_column( 0, 0, 9.09 )
sheetb.set_column( 1, 1, 13.91 )
sheetb.set_column( 2, 5, 9.91 )





drtot = 0
crtot = 0
batot = 0
r = 5
br = 5
for t in o.taccline_s:
    sheet.write(r, 0, t.docdate, df)
    sheet.write(r, 1, "", nf )
    sheet.write(r, 3, "", nf )
    sheet.write(r, 4, "", nf )
    sheet.write(r, 5, "", nf )
    if t.ref_:
        sheet.write(r, 1, t.ref_.name, border)
    sheet.write(r, 2, t.docdesc, smallb)
    if t.amountdr > 0:
        sheet.write(r, 3, t.amountdr, nf )
    if t.amountcr > 0:
        sheet.write(r, 4, t.amountcr, nf )
    if t.baladjAmount != 0:
        sheet.write(r, 5, "", boldra)
        
        batot = batot + t.baladjAmount
        for i in range( 0, 6 ):
            sheetb.write( br, i, "", border )

        sheetb.write(br, 0, t.docdate, df)
        if t.ref_:
            sheetb.write(br, 1, t.ref_.name, border)
        if t.amountdr > 0:
            sheetb.write(br, 2, t.amountdr, nf)
        if t.amountcr > 0:
            sheetb.write(br, 3, t.amountcr, nf)
        sheetb.write(br, 5, t.baladjAmount, nf)
        br = br + 1

    drtot = drtot + t.amountdr
    crtot = crtot + t.amountcr
    r = r + 1

for i in range( 0, 6 ):
    sheet.write( r, i, "", border )
    sheet.write( r+1, i, "", border )
    
sheet.write(r, 3, drtot, nft)
sheet.write(r, 4, crtot, nft)
r = r + 1
if drtot > crtot:
    sheet.write(r, 3, drtot - crtot, nft)
else:
    sheet.write(r, 4, crtot - drtot, nft)

sheetb.write(br, 5, batot, nft)

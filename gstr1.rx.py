df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'green'})
sheet = workbook.add_worksheet( "EAWV" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "GSTR1 Report")
sheet.write(1, 0, "From:", bold)
sheet.write_datetime(1, 1, o.fromdate, df)
sheet.write(2, 0, "To:", bold)
sheet.write(2, 1, o.todate, df)

dr = self.env['simrp.invoice'].search( [ ( 'invdate','>=',o.fromdate ), ( 'invdate','<=',o.todate ), ( 'state','=','i' ) ] )

sheet.write(4, 0, "Inv. No.", bold)
sheet.write(4, 1, "Inv. Date", bold)
sheet.write(4, 2, "Party Name", bold)
sheet.write(4, 3, "Party GST", bold)
sheet.write(4, 4, "Item Name", bold)
sheet.write(4, 5, "Item HSN", bold)
sheet.write(4, 6, "Item UOM", bold)
sheet.write(4, 7, "Qty", bold)
sheet.write(4, 8, "Rate", bold)
sheet.write(4, 9, "Inv. Amt.", bold)
sheet.write(4, 10, "Ewaybill No.", bold)

aline = {}
c = 11
for d in dr:
    for al in d.accline_s:
        if al.account_.type != 'p':
            aid = al.account_.id
            if aid not in aline.keys():
                aline[ aid ] = c
                sheet.write(4, c, al.account_.name, bold)
                c = c + 1
        
r = 5
for d in dr:
    sheet.write(r, 0, d.name)
    sheet.write(r, 1, d.invdate, df)
    sheet.write(r, 2, d.party_.name)
    sheet.write(r, 3, d.party_.gstno)
    # sheet.write(r, 4, d.item_.name)
    # sheet.write(r, 5, d.item_.hsnsac)
    # sheet.write(r, 6, d.item_.uom_.gstr1code)
    # sheet.write(r, 7, d.okoutqty, nf)
    # sheet.write(r, 8, d.rate, nf)
    sheet.write(r, 9, d.invamt, nf)
    if d.eway:
        sheet.write(r, 10, d.eway)

    for al in d.accline_s:
        if al.account_.type != 'p':
            aid = al.account_.id
            sheet.write(r, aline[ aid ], al.amountdr + al.amountcr)

    r = r+1

cname = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ']

sheet.write_formula(r, 9, '=SUM(J6:J' + str(r) + ')', nft)
for aid in aline.keys():
    sheet.write_formula(r, aline[ aid ], '=SUM(' + cname[ aline[ aid ] ] + '6:' + cname[ aline[ aid ] ] + str(r) + ')', nft)

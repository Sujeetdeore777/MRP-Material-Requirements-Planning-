df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'green'})
sheet = workbook.add_worksheet( "EAWV" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "GSTR3B Report")
sheet.write(1, 0, "From:", bold)
sheet.write_datetime(1, 1, o.fromdate, df)
sheet.write(2, 0, "To:", bold)
sheet.write(2, 1, o.todate, df)

dr = self.env['simrp.purchase'].search( [ ( 'docdate','>=',o.fromdate ), ( 'docdate','<=',o.todate ) ] )
# er = self.env['simrp.indirectexpense'].search( [ ( 'docdate','>=',o.fromdate ), ( 'docdate','<=',o.todate ) ] )

sheet.write(4, 0, "Inv. No.", bold)
sheet.write(4, 1, "Inv. Date", bold)
sheet.write(4, 2, "Party Name", bold)
sheet.write(4, 3, "Party GST", bold)
sheet.write(4, 4, "Party Doc Value", bold)
sheet.write(4, 5, "Purchase Code", bold)

aline = {}
c = 6
for d in dr:
    for al in d.accline_s:
        if al.account_.type != 'p':
            aid = al.account_.id
            if aid not in aline.keys():
                aline[ aid ] = c
                sheet.write(4, c, al.account_.name, bold)
                c = c + 1

# for d in er:
    # for al in d.accline_s:
        # if al.account_.type != 'p':
            # aid = al.account_.id
            # if aid not in aline.keys():
                # aline[ aid ] = c
                # sheet.write(4, c, al.account_.name, bold)
                # c = c + 1
        
r = 5
for d in dr:
    sheet.write(r, 0, d.docno)
    sheet.write(r, 1, d.docdate, df)
    sheet.write(r, 2, d.party_.name)
    sheet.write(r, 3, d.party_.gstno)
    sheet.write(r, 4, d.matchnet, nf)
    sheet.write(r, 5, d.name)

    for al in d.accline_s:
        if al.account_.type != 'p':
            aid = al.account_.id
            sheet.write(r, aline[ aid ], al.amountdr + al.amountcr)

    r = r+1

r = r + 1
# for d in er:
    # sheet.write(r, 0, d.docno)
    # sheet.write(r, 1, d.docdate, df)
    # sheet.write(r, 2, d.party_.name)
    # sheet.write(r, 3, d.party_.gstno)
    # sheet.write(r, 4, d.netamount, nf)
    # sheet.write(r, 5, d.name)

    # for al in d.accline_s:
        # if al.account_.type != 'p':
            # aid = al.account_.id
            # sheet.write(r, aline[ aid ], al.amountdr + al.amountcr)

    # r = r+1

cname = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ','BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ']

sheet.write_formula(r, 4, '=SUM(E6:E' + str(r) + ')', nft)
for aid in aline.keys():
    sheet.write_formula(r, aline[ aid ], '=SUM(' + cname[ aline[ aid ] ] + '6:' + cname[ aline[ aid ] ] + str(r) + ')', nft)

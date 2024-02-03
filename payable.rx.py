df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
nfi = workbook.add_format({'num_format': '0'})
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'green'})
sheet = workbook.add_worksheet( "Payables" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Payables Report")
sheet.write(1, 0, "As on:", bold)
sheet.write(1, 1, o.todate, df)
#sheet.write(2, 0, "To:", bold)
#sheet.write(2, 1, o.todate, df)

parties = self.env['simrp.party'].search( [], order='name' )

sheet.write(4, 0, "Party Name", bold)
sheet.write(4, 1, "Credit", bold)
sheet.write(4, 2, "Due upto", bold)
sheet.write(4, 3, "Due Amt", bold)
sheet.write(4, 4, "Ledger Dr", bold)
sheet.write(4, 5, "Ledger Cr", bold)
sheet.write(4, 6, "", bold)
sheet.write(4, 7, "Transction", bold)
sheet.write(4, 8, "Doc. Date", bold)
sheet.write(4, 9, "Doc Dr.", bold)
sheet.write(4, 10, "Doc Cr", bold)
sheet.write(4, 11, "Bal. Amt.", bold)
sheet.write(4, 12, "Due Date", bold)
sheet.write(4, 13, "Due", bold)

sheet.set_column( 0, 0, 35 )

r = 6

cnt = 0
payt = 0
duet = 0
for p in parties:
    acclines = self.env['simrp.accline'].search( [ ( 'account_', '=', p.account_.id ), ( 'baladjAmount', '!=', 0 ) ], order='amountdr desc, docdate' )
    acr = 0
    adr = 0
    ba = 0
    dueamt = 0
    for d in acclines:
        adr = adr + d.amountdr
        acr = acr + d.amountcr
        ba = ba + d.baladjAmount
        
    #pay = acr - adr
    if ba < -1:
        sheet.write(r, 0, p.name)
        sheet.write(r, 1, p.creditperiod, nfi)
        #sheet.write(r, 5, pay, nf)
        sheet.write(r, 5, ba, nf)
        
        crow = r
        cnt = cnt + 1
        payt = payt + ba
        for d in acclines:
            if d.ref_:
                sheet.write(r, 7, d.ref_.name)
            sheet.write(r, 8, d.docdate, df)
            if d.amountdr > 0:
                sheet.write(r, 9, d.amountdr, nf)
            if d.amountcr > 0:
                sheet.write(r, 10, d.amountcr, nf)
            sheet.write(r, 11, d.baladjAmount, nf)
            if d.baladjAmount > 0:
                dueamt = dueamt + d.baladjAmount
            if d.duedate:
                if d.amountdr == 0:
                    sheet.write(r, 12, d.docdate + datetime.timedelta(days=p.creditperiod), df)
                    if ( d.docdate + datetime.timedelta(days=p.creditperiod) ) < o.todate:
                        sheet.write(r, 13, 'due' )
                        dueamt = dueamt + d.baladjAmount
            r = r + 1
            
        sheet.write(crow, 2, o.todate - datetime.timedelta(days=p.creditperiod), df )
        sheet.write(crow, 3, dueamt, nf )
        
        duet = duet + dueamt
        
        #r = r + 1
    """
    sheet.write(r, 1, d.account_.name)
    sheet.write(r, 2, d.duedate, df)
    sheet.write(r, 3, d.newrefname)
    sheet.write(r, 4, d.amountdr, nf)
    sheet.write(r, 5, d.amountcr, nf)
    """

sheet.write(3, 1, "<<Total>>", bold)
sheet.write(3, 0, cnt, nfi)
sheet.write(3, 3, duet, nf)
sheet.write(3, 5, payt, nf)

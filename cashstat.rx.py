df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
sheet = workbook.add_worksheet( "Cash Transaction" )
sheet0 = workbook.add_worksheet( "Cash Ledger" )
sheet2 = workbook.add_worksheet( "Cash Log" )
center_format=workbook.add_format({
                            'align': 'center'
                           })

sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Statement Of Cash")
sheet.write(1, 0, "From:", bold)
sheet.write_datetime(1, 1, o.fromdate, df)
sheet.write(2, 0, "To:", bold)
sheet.write(2, 1, o.todate, df)

sheet.set_column(0, 5,18)

sheet.write(4, 1, "Cash Ledger", bold)
sheet.write(4, 2, "Opening Balance", bold)
sheet.write(4, 3, "Total In", bold)
sheet.write(4, 4, "Total Out", bold)
sheet.write(4, 5, "Closing Balance", bold)

sheet0.write(0, 0, "Report", bold)
sheet0.write(0, 1, "CASH LEDGER RECORDS",bold)
sheet0.write(1, 0, "From:", bold)
sheet0.write_datetime(1, 1, o.fromdate, df)
sheet0.write(2, 0, "To:", bold)
sheet0.write(2, 1, o.todate, df)

sheet0.set_column(0, 8,18)

r = 6
r1 = 6
cashAllAccount = self.env['simrp.account'].search( [ ( 'type','=','cash' ) ] )
for d in cashAllAccount:
    amt_debit = 0.0
    amt_debit1 = 0.0
    amt_credit = 0.0
    amt_credit1 = 0.0
    opbalance = 0.0
    sheet.write(r, 1, d.name)
    sheet0.write(r1, 0, d.name,bold)
    r1 = r1 + 1
    sheet0.write(r1, 1, "Doc Date", bold)
    sheet0.write(r1, 2, "Name", bold)
    sheet0.write(r1, 3, "Amount Debit", bold)
    sheet0.write(r1, 4, "Amount Credit", bold)
    sheet0.write(r1, 5, "Expense Head", bold)
    sheet0.write(r1, 6, "Description", bold)
    sheet0.write(r1, 7, "Balance", bold)
    r1 = r1 + 1
    Opening_balance = self.env['simrp.accline'].search( [ ('docdate', '<', o.fromdate), ( 'account_','=', d.name ) ] )
    for a in Opening_balance:
        amt_debit = amt_debit + a.amountdr
        amt_credit = amt_credit + a.amountcr
    opbalance = amt_debit - amt_credit
    sheet.write(r, 2, opbalance,nf)
    sheet0.write(r1, 1, o.fromdate,df)
    sheet0.write(r1, 7, opbalance,nf)
    sheet0.write(r1, 8, "Opening Balance",bold)
    r1 = r1 + 1
    close_balance = opbalance
    for dt in rrule(DAILY, dtstart=o.fromdate, until=o.todate):
        dr = self.env['simrp.accline'].search( [ ('docdate','=',dt ), ( 'account_','=',d.name ) ] )
        for c in dr:
            sheet0.write(r1, 1,c.docdate,df)
            sheet0.write(r1, 2,c.ref_.name)
            sheet0.write(r1, 3, c.amountdr,nf)
            sheet0.write(r1, 4, c.amountcr,nf)
            if not c.cash_.exp_head.name:
                sheet0.write(r1, 5, '')
            else:
                sheet0.write(r1, 5, c.cash_.exp_head.name)
            sheet0.write(r1, 6, c.cash_.Description)
            amt_debit1 = amt_debit1 + c.amountdr
            amt_credit1 = amt_credit1 + c.amountcr
            if c.amountdr > 0:
                close_balance = close_balance + c.amountdr
            else:
                close_balance = close_balance - c.amountcr
            sheet0.write(r1, 7, close_balance,nf)
            r1 = r1 + 1
        clbalance = opbalance + ( amt_debit1 - amt_credit1 )
    sheet.write(r, 3, amt_debit1,nf)
    sheet.write(r, 4, amt_credit1,nf)
    sheet.write(r, 5, clbalance,nf)
    sheet0.write(r1, 1, o.todate,df)
    sheet0.write(r1, 7, clbalance,nf)
    sheet0.write(r1, 8, "Closing Balance",bold)
    r = r + 1
    r1 = r1 + 2


sheet2.write(0, 0, "Report", bold)
sheet2.write(0, 1, "All Cash Transaction",bold)
sheet2.write(1, 0, "From:", bold)
sheet2.write_datetime(1, 1, o.fromdate, df)
sheet2.write(2, 0, "To:", bold)
sheet2.write(2, 1, o.todate, df)

sheet2.set_column(0, 7,20)
sheet2.write(4, 0, "Tx No", bold)
sheet2.write(4, 1, "Date", bold)
sheet2.write(4, 2, "Type", bold)
sheet2.write(4, 3, "Cash OUT A/c", bold)
sheet2.write(4, 4, "Cash IN A/c", bold)
sheet2.write(4, 5, "Out Amount", bold)
sheet2.write(4, 6, "Expenditure Head", bold)
sheet2.write(4, 7, "Description", bold)
sheet2.write(4, 7, "State", bold)


r = 6
for dt in rrule(DAILY, dtstart=o.fromdate, until=o.todate):
   dr = self.env['simrp.cash'].search( [ ( 'date','=',dt ) ] )
   for d in dr:
    sheet2.write(r, 0, d.name)
    sheet2.write(r, 1, d.date,df)
    sheet2.write(r, 2, d.type)
    sheet2.write(r, 3, d.cash_ledger_acc_out.name,center_format)
    if not d.cash_ledger_acc_in.name:
        sheet2.write(r, 4, '')
    else:
        sheet2.write(r, 4, d.cash_ledger_acc_in.name,center_format)
    sheet2.write(r, 5, d.out_amount, nf)
    if not d.exp_head.name:
        sheet2.write(r, 6, '')
    else:
        sheet2.write(r, 6, d.exp_head.name,center_format)
    sheet2.write(r, 7, d.Description)
    sheet2.write(r, 7, d.state)
    r = r + 1

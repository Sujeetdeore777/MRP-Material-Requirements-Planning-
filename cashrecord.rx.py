df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})

colorg_format=workbook.add_format({
                            'bg_color':'#7FE817',
                            'num_format': '0.00'
                           })
colord_format=workbook.add_format({
                            'bg_color':'#E77471',
                            'num_format': '0.00'
                           })
sheet = workbook.add_worksheet( "Expense Report" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Cash Expense Reports")
sheet.write(1, 0, "From:", bold)
sheet.write_datetime(1, 1, o.fromdate, df)
sheet.write(2, 0, "To:", bold)
sheet.write(2, 1, o.todate, df)

sheet.set_column(0, 7,20)
expenseAllAccount = self.env['simrp.account'].search( [ ( 'type','=','ex' ) ] )

sheet.write(4, 0, "Expense Head", bold)
sheet.write(4, 1, "Monthly Budget", bold)
sheet.write(4, 2, "Total Cash Spend", bold)
sheet.write(4, 3, "Total Fund Spend", bold)
sheet.write(4, 4, "Total Purchase Spend", bold)
sheet.write(4, 5, "Other Spend", bold)
sheet.write(4, 6, "Total Spend", bold)
sheet.write(4, 7, "Budget Variance", bold)

acclist = []
for d in expenseAllAccount:
    acclist.append( d.id )
ar = self.env[ 'simrp.accline' ].search( [ ( 'account_','in', acclist ), '|', ( 'docdate','>=',o.fromdate ), ( 'docdate','<=',o.todate ) ] )

r = 6
Tx = 0
Ftn = 0
Iexp = 0
Other = 0
alltotal = 0
for d in expenseAllAccount:
    adr_IExp = 0
    acr_IExp = 0
    adr_Tx = 0
    acr_Tx = 0
    adr_FTN = 0
    acr_FTN = 0
    adr_o = 0
    acr_o = 0
    sheet.write(r, 0, d.name)
    sheet.write(r, 1, d.monthly_budget)
    # for dt in rrule(DAILY, dtstart=, until=):
        # ar = self.env['simrp.accline'].search( [ ( 'docdate','=',dt ), ( 'account_','=',d.name ) ] )
    for a in ar:
        if a.account_.id == d.id:
            txt = a.ref_.name
            x = txt.split("-")
            if x[0] in ['IExp', 'PUR']:
                adr_IExp = adr_IExp + a.amountdr
                acr_IExp = acr_IExp + a.amountcr
            elif x[0] == 'CTX':
                adr_Tx = adr_Tx + a.amountdr
                acr_Tx = acr_Tx + a.amountcr
            elif x[0] == 'FTN':
                adr_FTN = adr_FTN + a.amountdr
                acr_FTN = acr_FTN + a.amountcr
            else:
                adr_o = adr_o + a.amountdr
                acr_o = acr_o + a.amountcr
    Iexp_total = 0
    Iexp_total = adr_IExp - acr_IExp
    Tx_total = 0
    Tx_total = adr_Tx - acr_Tx
    FTN_total = 0
    FTN_total = adr_FTN - acr_FTN
    other_total = 0
    other_total = adr_o - acr_o
    Tx = Tx + Tx_total
    Ftn = Ftn + FTN_total
    Other = Other + other_total
    Iexp = Iexp + Iexp_total
    sheet.write(r, 2, Tx_total, nf)
    sheet.write(r, 3, FTN_total, nf)
    sheet.write(r, 4, Iexp_total, nf)
    sheet.write(r, 5, other_total, nf)
    total = 0
    total = Tx_total + FTN_total + Iexp_total + other_total
    alltotal = alltotal + total
    sheet.write(r, 6, total, nf)
    per = 0
    if d.monthly_budget > 0:
        per = ( total / d.monthly_budget ) * 100
        if per < 100:
            sheet.write(r, 7, str(per)+"%",colorg_format)
        else:
            sheet.write(r, 7, str(per)+"%",colord_format)
    r = r + 1
r = r + 1
sheet.write(r,0," Total ",bold)
sheet.write(r, 2, Tx, nf)
sheet.write(r, 3, Ftn, nf) 
sheet.write(r, 4, Iexp, nf) 
sheet.write(r, 5, Other, nf) 
sheet.write(r, 6, alltotal) 

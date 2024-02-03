df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'green'})
sheet = workbook.add_worksheet( "CLBAL" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Closing Balance Report")
sheet.write(1, 0, "As on 31.03.2020", bold)
#sheet.write_datetime(1, 1, o.fromdate, df)
#sheet.write(2, 0, "To:", bold)
#sheet.write(2, 1, o.todate, df)

dr = self.env['simrp.accline'].search( [ ( 'closingbalance_','!=',False ) ] )

sheet.write(4, 0, "Entry Date", bold)
sheet.write(4, 1, "Party Name", bold)
sheet.write(4, 2, "Due. Date", bold)
sheet.write(4, 3, "Ref. Name", bold)
sheet.write(4, 4, "Amount Dr", bold)
sheet.write(4, 5, "Amount Cr", bold)

r = 6
acr = 0
adr = 0
for d in dr:
    sheet.write(r, 0, d.tdate, df)
    sheet.write(r, 1, d.account_.name)
    sheet.write(r, 2, d.duedate, df)
    sheet.write(r, 3, d.newrefname)
    sheet.write(r, 4, d.amountdr, nf)
    sheet.write(r, 5, d.amountcr, nf)
    adr = adr + d.amountdr
    acr = acr + d.amountcr
    r = r + 1

sheet.write(r, 1, "Total", bold)
sheet.write(r, 4, adr, nf)
sheet.write(r, 5, acr, nf)

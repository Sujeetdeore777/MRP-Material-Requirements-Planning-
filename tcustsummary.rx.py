df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'yellow'})
bold = workbook.add_format({'bg_color': '#bfbfbf', 'border': 1,'align': 'center', 'valign': 'vcenter', 'font_size':10,})
sheet = workbook.add_worksheet( "Customer Outstanding" )
sheet.write(0, 0, "Date:", bold)
sheet.write(0, 1, o.currentdate, df)

heading_format  = workbook.add_format({
    'border': 1,
    'bg_color':'#000000',
    'align': 'center',
    'valign': 'vcenter',
    'font_size':12,
    'font_color' : '#ffffff'
    })
color_format=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#DFC5D4',
                            'num_format': '0.00',
                            'font_size':10
                           })
color_format1=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#E8DAE3',
                            'num_format': '0.00',
                            'font_size':10
                           })
color_format2=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#EEEEEE',
                            'num_format': '0.00',
                            'font_size':10
                           })
                           
sheet.merge_range('A2:M2', "", heading_format)

sheet.set_column(0,0,30)
sheet.set_column(2,2,12)
sheet.set_column(2,3,10)
sheet.set_column(2,4,10)
sheet.set_column(2,5,10)
sheet.set_column(2,6,10)
sheet.set_column(2,7,13)
sheet.set_column(2,8,13)
sheet.set_column(2,9,13)
sheet.set_column(2,10,13)
sheet.set_column(2,11,13)
sheet.set_column(2,12,13)

sheet.write(1, 0, "Customer Outstanding Summary Report", heading_format)
sheet.write(3, 0, "Customer name", color_format)
sheet.write(3, 1, "Credit days", color_format)
sheet.write(3, 2, "Ledger balance", color_format)
sheet.write(3, 3, "Bills Adj.", color_format)
sheet.write(3, 4, "Difference", color_format)
sheet.write(3, 5, "Undue Bills", color_format)
sheet.write(3, 6, "Overdue Amt.", color_format)
sheet.write(3, 7, "before 15 days", color_format)
sheet.write(3, 8, "15 days overdue", color_format)
sheet.write(3, 9, "30 days overdue", color_format)
sheet.write(3, 10, "60 days overdue", color_format)
sheet.write(3, 11, "90 days overdue", color_format)
sheet.write(3, 12, "Unadj. payments", color_format)

r = 4
for s in o.tcustsummaryline:
    sheet.write(r, 0, s.party_.name, color_format1)
    sheet.write(r, 1, s.creditperiod, color_format2)
    sheet.write(r, 2, s.balance, color_format2)
    sheet.write(r, 3, s.badj, color_format2)
    sheet.write(r, 4, s.diff, color_format2)
    sheet.write(r, 5, s.unduebills, color_format2)
    sheet.write(r, 6, s.dueamount, color_format2)
    sheet.write(r, 7, s.ageing15days, color_format2)
    sheet.write(r, 8, s.ageing15daysoverdue, color_format2)
    sheet.write(r, 9, s.ageing30daysoverdue, color_format2)
    sheet.write(r, 10, s.ageing60daysoverdue, color_format2)
    sheet.write(r, 11, s.ageing90daysoverdue, color_format2)
    sheet.write(r, 12, s.unadjpayments, color_format2)
    r = r + 1
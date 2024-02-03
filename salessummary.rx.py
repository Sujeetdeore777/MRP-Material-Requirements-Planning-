df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
nft = workbook.add_format({'num_format': '0.00', 'bg_color': 'yellow'})
bold = workbook.add_format({'bg_color': '#bfbfbf', 'border': 1,'align': 'center', 'valign': 'vcenter', 'font_size':10,})
sheet = workbook.add_worksheet( "Sale Order Summary" )

custsummary = json.loads(o.reporthtml)
quarter = json.loads(o.reporthtm)

heading_format  = workbook.add_format({
    'border': 1,
    'bg_color':'#000000',
    'align': 'center',
    'valign': 'vcenter',
    'font_size':10,
    'font_color' : '#ffffff'
    })
heading_format1  = workbook.add_format({
    'border': 1,
    'bg_color':'#737373',
    'align': 'center',
    'valign': 'vcenter',
    'font_size':10,
    'font_color' : '#ffffff'
    })
heading_format3  = workbook.add_format({
    'border': 1,
    'bg_color':'#bfbfbf',
    'align': 'Left',
    'valign': 'vcenter',
    'font_size':10
    })
annual_format  = workbook.add_format({
    'border': 1,
    'bg_color':'yellow',
    'align': 'center',
    'valign': 'vcenter',
    'font_size':10
    })

color_format=workbook.add_format({
                            'border': 1,
                            'align': 'Left',
                            'bg_color':'#ffe5b4',
                            'font_size':8
                           })
color_format1=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#e6e6ff',
                            'num_format': '0.00',
                            'font_size':8
                           })
color_format2=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#9EC3E2',
                            'num_format': '0.00',
                            'font_size':8
                           })
color_format3=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#92A2B1',
                            'num_format': '0.00',
                            'font_size':8
                           })
color_format4=workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'bg_color':'#b3e6b3',
                            'num_format': '0.00',
                            'font_size':8
                           })

format5 = workbook.add_format({'bg_color': '#e9f0fc', 'border':1})
format1 = workbook.add_format({'bg_color': '#d2e0f9'})
format2 = workbook.add_format({'bg_color': '#ccccff'})
format3 = workbook.add_format({'bg_color': '#e6e6ff'})
format4 = workbook.add_format({'bg_color': '#d9ffcc'})

sheet.merge_range('A1:N1', "", heading_format)
sheet.merge_range('A2:N2', "", heading_format1)
r = 3

sheet.write(0, 0, "Jia Industries - Sales Summary", heading_format)
sheet.write(1, 0, "FY 2022-2023 [ Internal Analysis]", heading_format1)
sheet.write(2, 0, "Customer Name", heading_format3)
sheet.write(2, 13, "Total", heading_format3)

sheet.set_column(0,0,15)

for cust in custsummary:
    for p in custsummary[cust]:
        row = 0
        sheet.write(r, 0, p, color_format)
        c = 1
        for cl in custsummary[cust][p]:
            for o in custsummary[cust][p][cl]:
                sheet.write(2, c, cl, bold)
                for val in custsummary[cust][p][cl].values():
                    sheet.write(r, c,str(round(val / 100000, 1))+"Lacs" , format5)
                    row = row + val
            c = c + 1
        sheet.write(r, c, str(round(row / 100000, 1))+"Lacs", annual_format)
        r = r + 1
sheet.write(r, 0, "Quarter", heading_format3)

qval1 = 0
for qv in quarter["q1"].values():
    qval1 = qval1 + qv
r = r + 1
sheet.merge_range('B'+str(r)+':D'+str(r), str(round(qval1 / 100000, 1))+"Lacs", color_format1)
# sheet.write(r, 1, qval1)

qval2 = 0
for qv2 in quarter["q2"].values():
    qval2 = qval2 + qv2
sheet.merge_range('E'+str(r)+':G'+str(r), str(round(qval2 / 100000, 1))+"Lacs", color_format2)

qval3 = 0
for qv3 in quarter["q3"].values():
    qval3 = qval3 + qv3
sheet.merge_range('H'+str(r)+':J'+str(r), str(round(qval3 / 100000, 1))+"Lacs", color_format3)

qval4 = 0
for qv4 in quarter["q4"].values():
    qval4 = qval4 + qv4
sheet.merge_range('K'+str(r)+':M'+str(r), str(round(qval4 / 100000, 1))+"Lacs", color_format4)

sheet.write(r, 0, "Annual", heading_format3)

total = 0
for q in quarter:
    for val1 in quarter[q].values():
        total = total + val1
r = r + 1
sheet.merge_range('B'+str(r)+':M'+str(r), str(round(total / 10000000, 1))+"Cr", annual_format)

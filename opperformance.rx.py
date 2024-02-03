df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})


color_format=workbook.add_format({
                            'border': 1,
                            'align': 'Right',
                            'bg_color':'#FDFAB6',
                            'num_format': '0.00'
                           })

cell_format  = workbook.add_format({
    'border': 1,
    'align': 'center',
    'bg_color':'#060600',
    'valign': 'vcenter',
    'font_size':12
    })

cell_format_p  = workbook.add_format({
    'border': 1,
    'bold': True,
    'align': 'center',
    'valign': 'vcenter',
    'font_size':9,
    'font_color':'#565051'
    })

cell_format_rr  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'bg_color':'#A0A7A8',
    'font_size':12
    })

cell_format_r  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'num_format': '0.00',
    'font_size':12
    })

cell_format_r_zero  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'bg_color':'#88E7F2',
    'font_size':12
    })

cell_format_clr  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'bg_color':'yellow',
    'font_size':12
    })

cell_format_sat  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'bg_color':'#082D58',
    'font_size':12
    })

sheet = workbook.add_worksheet( "opperformance" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Performance Report")
sheet.write(1, 0, "Month Date:", bold)
sheet.write(1, 1, o.sdate, df)
sheet.set_column(0,0,20)
c = 5
while(c < 70):
    sheet.set_column(c,c,6)
    c = c + 1

r = 4
dphp = json.loads( o.datadicperformance )
for i in dphp:
    cnt = 0
    for v in dphp[i]:
        if str(v) == 'name' or str(v) == 'workexpect' or str(v) == 'totalworkhours' or str(v) == 'total' or str(v) == 'percent':
            sheet.write(r, cnt, str(v), bold)
            cnt = cnt + 1
        else:
            sheet.write(r, cnt, str(v), bold)
            cnt = cnt + 1
    break

sheet.freeze_panes(5, 0)
r = 5
for i in dphp:
    _logger.info(dphp[i]['name'])
    cnt = 0 
    totalmonthavgper = 0
    totalcnt = 0
    for v in dphp[i]:
        if str(v) == 'name' or str(v) == 'workexpect' or str(v) == 'totalworkhours' or str(v) == 'total' or str(v) == 'percent':
            if v == 'name':
                sheet.write(r, cnt, dphp[i][v], color_format)
            elif v == 'totalworkhours':
                sheet.write(r, cnt, dphp[i][v], cell_format_rr)
            elif v == 'workexpect':
                sheet.write(r, cnt, dphp[i][v], cell_format_rr)
            elif v == 'total':
                sheet.write(r, cnt, str(dphp[i][v]), cell_format_rr) 
            elif v == 'percent':
                sheet.write(r, cnt, str(dphp[i][v])+"%", cell_format_rr) 
            cnt = cnt + 1
        else:
            for j in dphp[i][v]:
                if j == 'p':
                    prd_hr = (dphp[i][v][j] /60) /60
                    sheet.write(r, cnt, float(round(prd_hr, 2)), cell_format_p)
                else:
                    totalmonthavgper = totalmonthavgper + dphp[i][v][j]
                    if round(dphp[i][v][j],2) > 0:
                        totalcnt = totalcnt + 1
                    sheet.write(r, cnt, float(round(dphp[i][v][j], 2)), cell_format_r)
                cnt =cnt + 1
            _logger.info(totalmonthavgper)
    if (totalcnt > 0) and (dphp[i]['totalworkhours'] > 0):
        avg = totalmonthavgper / totalcnt
        sheet.write(r, 3, str(float(round(avg, 2))), cell_format_rr)
        per = round((avg/dphp[i]['totalworkhours'])*100,2)
        sheet.write(r, 4, str(int(round(per, 2)))+"%", cell_format_rr) 
    r = r + 1

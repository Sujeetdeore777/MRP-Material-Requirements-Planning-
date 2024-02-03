df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})

color_format=workbook.add_format({
                            'border': 1,
                            'align': 'Right',
                            'bg_color':'#FDFAB6',
                            'num_format': '0.00'
                           })
colord_format=workbook.add_format({
                            'border': 1,
                            'align': 'Right',
                            'bg_color':'#E77471',
                            'num_format': '0.00'
                           })

heading_format  = workbook.add_format({
    'border': 1,
    'bg_color':'#060600',
    'align': 'center',
    'valign': 'vcenter',
    'font_size':12,
    'font_color' : '#FAFAF2'
    })


cell_format  = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
    'font_size':10
    })

cell_format_l  = workbook.add_format({
    'border': 1,
    'align': 'Left',
    'valign': 'vcenter',
    'font_size':12
    })

cell_format_r  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'font_size':12
    })
sheet = workbook.add_worksheet( "Uniform" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Uniform Reports")
sheet.write(1, 0, "Date:", bold)
sheet.write(1, 1, o.date, df)
sheet.write(2, 0, "trainee days:", bold)
sheet.write(2, 1, o.trainee_day)
sheet.write(3, 0, "Re-issue:", bold)
sheet.write(3, 1, o.Reissue_interval)

sheet.set_column(0, 5,25)

sheet.write(5, 0, "Sr. No", bold)
sheet.write(5, 1, "Employee Name", bold)
sheet.write(5, 2, "Last Issue date", bold)
sheet.write(5, 3, "New Issue(Y/N)", bold)
sheet.write(5, 4, "Reissue (Y/N)", bold)

r = 6
srno = 1
emp = self.env['simrp.employee'].search( [ ( 'active','=',True ) ] )
for a in emp:
    sheet.write(r, 0, srno,cell_format) 
    sheet.write(r, 1, a.name,cell_format_l) 
    sheet.write(r, 2, a.lastuniformissue,color_format)
    if a.lastuniformissue:
        d = o.date - a.lastuniformissue
        if d.days >= o.Reissue_interval:
            sheet.write(r,3,'N',color_format)
            sheet.write(r,4,'Y',color_format)
        else:
            sheet.write(r,3,'N',color_format)
            sheet.write(r,4,'N',color_format)
    else:
        d = o.date - a.doj
        if d.days >= o.trainee_day:
            sheet.write(r,3,'Y',color_format)
        else:
            sheet.write(r,3,'N',color_format)
        sheet.write(r,4,'N',color_format)
    srno = srno + 1
    r = r + 1
df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})

color_format=workbook.add_format({
                            'border': 1,
                            'align': 'Right',
                            'bg_color':'#FDFAB6',
                            'num_format': '0.00',
                            'font_size':8
                           })

color_format_green = workbook.add_format({
                            'border': 1,
                            'align': 'Right',
                            'bg_color':'#A2D9CE',
                            'num_format': '0.00',
                            'font_size':8
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
    'border': 1,
    'bg_color':'#B9B9B5',
    'align': 'center',
    'valign': 'vcenter',
    'font_size':8
    })

cell_format_l  = workbook.add_format({
    'border': 1,
    'align': 'Left',
    'valign': 'vcenter',
    'font_size':8
    })

cell_format_r  = workbook.add_format({
    'border': 1,
    'align': 'Right',
    'valign': 'vcenter',
    'font_size':8
    })

sheet = workbook.add_worksheet( "Register" )
sheet.set_column(0,0,0)
sheet.set_column(1, 1,14)
sheet.set_column(2, 12,7)
sheet.set_column(13, 17,5)
sheet.set_column(18, 22,7)
sheet.set_column(23, 24,5)

sheet.merge_range('F2:M2', "", cell_format)
sheet.merge_range('N2:U2', "", cell_format)
sheet.merge_range('X2:Y2', "", cell_format)
sheet.merge_range('F1:Y1', "", heading_format)
sheet.merge_range('B1:E1', "", heading_format)

sheet.write('F1:Y1', "Salary Statement - " + o.bu_.name, heading_format)
sheet.write('B1:E1',o.todate.month, heading_format)
sheet.write(1, 1, "", cell_format)
sheet.write(1, 2, "", cell_format)
sheet.write(1, 3, "", cell_format)
sheet.write(1, 4, "", cell_format)
sheet.write('F2:M2', "Pay", cell_format)
sheet.write('N2:U2', "Adjustments", cell_format)
sheet.write('X2:Y2', "Emplr Cont.", cell_format)
sheet.write(1, 21, "Net", cell_format)
sheet.write(1, 22, "Signature", bold)

sheet.write(2, 1, "Name", cell_format)
sheet.write(2, 2, "Salary", cell_format)
sheet.write(2, 3, "Days", cell_format)
sheet.write(2, 4, "Attend", cell_format)
sheet.write(2, 5, "Basic", bold)
sheet.write(2, 6, "HRA", bold)
sheet.write(2, 7, "Conv", bold)
sheet.write(2, 8, "Unifm", bold)
sheet.write(2, 9, "Med", bold)
sheet.write(2, 10, "OT", bold)
sheet.write(2, 11, "Pers", bold)
sheet.write(2, 12, "Gross", bold)
sheet.write(2, 13, "ESIC", cell_format)
sheet.write(2, 14, "PF", cell_format)
sheet.write(2, 15, "LWF", cell_format)
sheet.write(2, 16, "PT", cell_format)
sheet.write(2, 17, "TDS", cell_format)
sheet.write(2, 18, "Total", cell_format)
sheet.write(2, 19, "Adv", cell_format)
sheet.write(2, 20, "ADD", bold)
sheet.write(2, 21, "Pay", cell_format)
sheet.write(2, 22, "", bold)
sheet.write(2, 23, "ESIC", cell_format)
sheet.write(2, 24, "PF", cell_format)

r = 3
register_emp = self.env['simrp.salaryrecord'].search( [ ( 'monthempsalary_','=',o.monthempsalary_.id ), ( 'employee_.espf','=',True ),( 'employee_.active','=',True ),('bu_','=',o.bu_.id) ] )
gross = 0
total_esic = 0
total_pf = 0
total_lwf = 0
total_pt = 0
total_tds = 0
total = 0
total_add = 0
total_adv = 0
netpay = 0
totalesic_contri = 0
totalpf_contri = 0
for a in register_emp:
    sheet.write(r, 1, a.employee_.name,cell_format_l)
    if a.employee_.basewage != 0:
        sheet.write(r, 2, a.employee_.basewage,cell_format)
        sheet.write(r, 3, a.monthempsalary_.salary_days,color_format)
        sheet.write(r, 4, a.attend_register,color_format)
        sheet.write(r, 5, a.wages,color_format)
        sheet.write(r, 6, a.hra,color_format)
        sheet.write(r, 7, a.conv,color_format)
        sheet.write(r, 8, a.uniform,color_format)
        sheet.write(r, 9, a.medical,color_format)
        sheet.write(r, 10, a.others,color_format)
        sheet.write(r, 11, a.tds,color_format)
        gross = gross + a.grosspay
        sheet.write(r, 12, a.grosspay,color_format_green)
        total_esic = total_esic + a.esic
        sheet.write(r, 13, a.esic,cell_format_r)
        total_pf = total_pf + a.pf
        sheet.write(r, 14, a.pf,cell_format_r)
        total_lwf = total_lwf + a.lwf
        sheet.write(r, 15, a.lwf,cell_format_r)
        total_pt = total_pt + a.monthpt
        sheet.write(r, 16, a.monthpt,cell_format_r)
        total_tds = total_tds + a.tds
        sheet.write(r, 17, a.tds,cell_format_r)
        total = total + a.total_deduction
        sheet.write(r, 18, a.total_deduction,cell_format)
        total_adv = total_adv + a.adv_deduction
        sheet.write(r, 19, a.adv_deduction,cell_format_r)
        add = 0
        add = a.annual_bg + a.leave_encashment - a.addpenaltyreward
        total_add = total_add + add
        sheet.write(r, 20,add,color_format)
        pay = 0 
        pay = a.grosspay - a.total_deduction - a.adv_deduction + add
        netpay = netpay + pay
        sheet.write(r, 21, pay,color_format_green)
        signature = 0 
        signature = a.wages + a.conv + a.uniform + a.medical
        sheet.write(r, 22, signature,cell_format)
        totalesic_contri = totalesic_contri + a.esic_contri
        sheet.write(r, 23, a.esic_contri,cell_format_r)
        totalpf_contri = totalpf_contri + a.pf_contri
        sheet.write(r, 24, a.pf_contri,cell_format_r)
    else:
        raise exceptions.UserError('Base Wage is not entered for: ' + a.employee_.name )
    r = r + 1

sheet.write(r, 11, "Total",heading_format)
sheet.write(r, 12, gross, cell_format)
sheet.write(r, 13, total_esic, cell_format)
sheet.write(r, 14, total_pf, cell_format)
sheet.write(r, 15, total_lwf, cell_format)
sheet.write(r, 16, total_pt, cell_format)
sheet.write(r, 17, total_tds, cell_format)
sheet.write(r, 18, total, cell_format)
sheet.write(r, 19, total_adv, cell_format)
sheet.write(r, 20, total_add, cell_format)
sheet.write(r, 21, netpay, cell_format)
sheet.write(r, 22,"", cell_format)
sheet.write(r, 23, totalesic_contri, cell_format)
sheet.write(r, 24, totalpf_contri, cell_format)
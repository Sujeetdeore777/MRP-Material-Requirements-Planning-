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
sheet = workbook.add_worksheet( "Cash Salary" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Cash Salary Reports")
sheet.write(1, 0, "To:", bold)
sheet.write(1, 1, o.todate, df)

sheet.set_column(0, 0,20)
sheet.merge_range('A4:C4', "", heading_format)
sheet.merge_range('D4:G4', "", heading_format)
sheet.merge_range('H4:I4', "", heading_format)
sheet.merge_range('K4:N4', "", heading_format)

sheet.write('A4:C4', "", heading_format)
sheet.write('D4:G4', "Add", heading_format)
sheet.write('H4:I4', "Less", heading_format)
sheet.write('K4:N4', "Advance", heading_format)
sheet.write(3, 9, "", heading_format)

sheet.write(4, 0, "Name", bold)
sheet.write(4, 1, "Days", bold)
sheet.write(4, 2, "OT", bold)
sheet.write(4, 3, "Salary", bold)
sheet.write(4, 4, "Bonus", bold)
sheet.write(4, 5, "Leaves", bold)
sheet.write(4, 6, "Extra", bold)
sheet.write(4, 7, "Penalty", bold)
sheet.write(4, 8, "Adv", bold)
sheet.write(4, 9, "Pay", bold)
sheet.write(4, 10, "Opening", bold)
sheet.write(4, 11, "Given", bold)
sheet.write(4, 12, "Deduction", bold)
sheet.write(4, 13, "Balance", bold)

r = 5
cash_emp = self.env['simrp.salaryrecord'].search( [ ( 'month_end','=',o.todate ), ( 'employee_.espf','!=',True ),( 'employee_.active','=',True ) ] )
total_pay = 0
# for a in cash_emp:
    # sheet.write(r, 0, a.employee_.name,cell_format_l) 
    # sheet.write(r, 1, a.pay_days,color_format) 
    # sheet.write(r, 2, a.ot,color_format) 
    # sheet.write(r, 3, a.grosspay,color_format)
    # bonus = 0
    # bonus = a.annual_bg + a.stardays
    # sheet.write(r, 4, bonus,color_format) 
    # sheet.write(r, 5, a.leave_encashment,color_format) 
    # sheet.write(r, 6, a.add_nonslip,color_format) 
    # penalty = 0
    # penalty = a.addpenaltyreward + a.u_absent
    # sheet.write(r, 7, penalty,colord_format)
    # sheet.write(r, 8, a.adv_deduction,colord_format)
    # pay = 0 
    # pay = a.grosspay + bonus + a.leave_encashment + a.add_nonslip - penalty - a.adv_deduction
    # total_pay = total_pay + pay
    # sheet.write(r, 9, pay, color_format)
    # for dt in rrule(DAILY, dtstart=o.fromdate, until=o.todate):
        # advance = self.env['simrp.advance'].search( [ ('payment_date','=',dt ), ( 'employee_','=',a.employee_.id ),('status','=','o') ] )
        # adv_this_month = 0
        # for adv in advance:
            # adv_this_month = adv_this_month + adv.amount
        # sheet.write(r, 10, adv_this_month,cell_format_r)
    # advance_opening = self.env['simrp.advance'].search( [ ('payment_date','<=',o.fromdate ), ( 'employee_','=',a.employee_.id ),('status','=','o') ] )
    # adv_opening = 0
    # for adv in advance_opening:
        # adv_opening = adv_opening + adv.amount
    # sheet.write(r, 11, adv_opening, cell_format_r)
    # sheet.write(r, 12, a.adv_deduction, cell_format_r)
    # sheet.write(r, 13, a.advancebal, color_format)
    # r = r + 1

sheet.write(r, 9, total_pay,bold)
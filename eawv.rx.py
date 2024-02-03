df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
sheet = workbook.add_worksheet( "EAWV" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Employee Attendance-Work Variance")
sheet.write(1, 0, "From:", bold)
sheet.write_datetime(1, 1, o.fromdate, df)
sheet.write(2, 0, "To:", bold)
sheet.write(2, 1, o.todate, df)

sheet.write(4, 0, "Emp. Name", bold)
sheet.write(4, 1, "Total", bold)
c = 2
for dt in rrule(DAILY, dtstart=o.fromdate, until=o.todate):
    sheet.write(4, c, dt, workbook.add_format({'num_format': 'ddd dd/mm'}))
    c=c+2

emps = self.env['simrp.employee'].search( [ ( 'active','=',True ) ] )
r = 5
for e in emps:
    sheet.write(r, 0, e.name)
    c = 2
    for dt in rrule(DAILY, dtstart=o.fromdate, until=o.todate):
        ar = self.env['simrp.attendance'].search( [ ( 'adate','=',dt ), ( 'employee_','=',e.id ) ] )
        whr = ar.present * e.workhours + ar.ot + ar.hadj
        if whr > 0:
            sheet.write(r, c, whr, nf)

        prs = self.env['simrp.woproduction'].search( [ ( 'adate1','=',dt ), ( 'employee_','=',e.id ) ] )
        phr = 0
        for pr in prs:
            tdelta = shiftinfo.getShiftTimeDiff( pr.pstime, pr.petime, self.env.user.tz, 0, True )
            phr = phr + ( tdelta / 60 )
            
        if phr > 0:
            sheet.write(r, c+1, phr, nf)
        c=c+2
    r = r+1

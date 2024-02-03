df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0.00'})
sheet = workbook.add_worksheet( "ATT" )
sheet.write(0, 0, "Report", bold)
sheet.write(0, 1, "Attendance")
sheet.write(1, 0, "From:", bold)
sheet.write_datetime(1, 1, o.fromdate, df)
sheet.write(2, 0, "To:", bold)
sheet.write(2, 1, o.todate, df)

sheet.write(4, 0, "Emp. Name", bold)
sheet.write(4, 1, "Total", bold)

emps = self.env['simrp.employee'].search( [ ( 'active','=',True ) ] )
r = 5
for e in emps:
    sheet.write(r, 0, e.name)
    p = 0
    ot = 0
    for dt in rrule(DAILY, dtstart=o.fromdate, until=o.todate):
        ar = self.env['simrp.attendance'].search( [ ( 'adate','=',dt ), ( 'employee_','=',e.id ) ] )
        #_logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(ar.id) )
        if ar:
            p = p + ar.present
            ot = ot + ar.ot + ar.hadj


    if p > 0:
        sheet.write(r, 1, p, nf)
        sheet.write(r, 2, ot, nf)
    r = r+1

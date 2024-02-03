sheet = book.sheet_by_name( 'B2B' )
for l in range(6, sheet.nrows):
    _logger.info( "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< " + str(sheet.cell( l, 8 ).value) + " " + str(l) )
    if (isinstance(sheet.cell( l, 8 ).value, float) ):
        self.env[ 'simrp.gstr2line' ].create( {
            'gstr2_': o.id,
            'type': 'b2b',
            'gstin': sheet.cell( l, 0 ).value,
            'gstname': sheet.cell( l, 1 ).value,
            'invno': sheet.cell( l, 2 ).value,
            'doctype': 'Reg.Inv',
            'invdt': sheet.cell( l, 4 ).value,
            'invval': sheet.cell( l, 5 ).value,
            'totgst': ( sheet.cell( l, 10 ).value + sheet.cell( l, 11 ).value + sheet.cell( l, 12 ).value + sheet.cell( l, 13 ).value ),
            'itcavailable': sheet.cell( l, 16 ).value,
            'itcreason': sheet.cell( l, 17 ).value,
            'oinvno': '',
            'oinvdt': '' } )

sheet = book.sheet_by_name( 'B2BA' )
for l in range(7, sheet.nrows):
    if (isinstance(sheet.cell( l, 10 ).value, float)):
        self.env[ 'simrp.gstr2line' ].create( {
            'gstr2_': o.id,
            'type': 'b2ba',
            'gstin': sheet.cell( l, 2 ).value,
            'gstname': sheet.cell( l, 3 ).value,
            'invno': sheet.cell( l, 4 ).value,
            'doctype': 'Reg.Inv',
            'invdt': sheet.cell( l, 6 ).value,
            'invval': sheet.cell( l, 7 ).value,
            'totgst': ( sheet.cell( l, 12 ).value + sheet.cell( l, 13 ).value + sheet.cell( l, 14 ).value + sheet.cell( l, 15 ).value ),
            'itcavailable': sheet.cell( l, 18 ).value,
            'itcreason': sheet.cell( l, 19 ).value,
            'oinvno': sheet.cell( l, 0 ).value,
            'oinvdt': sheet.cell( l, 1 ).value } )

sheet = book.sheet_by_name( 'B2B-CDNR' )
for l in range(6, sheet.nrows):
    if (isinstance(sheet.cell( l, 9 ).value, float) ):
        self.env[ 'simrp.gstr2line' ].create( {
            'gstr2_': o.id,
            'type': 'b2bc',
            'gstin': sheet.cell( l, 0 ).value,
            'gstname': sheet.cell( l, 1 ).value,
            'invno': sheet.cell( l, 2 ).value,
            'doctype': sheet.cell( l, 3 ).value + " - " + sheet.cell( l, 4 ).value,
            'invdt': sheet.cell( l, 5 ).value,
            'invval': sheet.cell( l, 6 ).value,
            'totgst': ( sheet.cell( l, 11 ).value + sheet.cell( l, 12 ).value + sheet.cell( l, 13 ).value + sheet.cell( l, 14 ).value ),
            'itcavailable': sheet.cell( l, 17 ).value,
            'itcreason': sheet.cell( l, 18 ).value,
            'oinvno': '',
            'oinvdt': '' } )

sheet = book.sheet_by_name( 'B2B-CDNRA' )
for l in range(7, sheet.nrows):
    if (isinstance(sheet.cell( l, 12 ).value, float)):
        self.env[ 'simrp.gstr2line' ].create( {
            'gstr2_': o.id,
            'type': 'b2bca',
            'gstin': sheet.cell( l, 3 ).value,
            'gstname': sheet.cell( l, 4 ).value,
            'invno': sheet.cell( l, 5 ).value,
            'doctype': sheet.cell( l, 6 ).value + " - " + sheet.cell( l, 7 ).value,
            'invdt': sheet.cell( l, 8 ).value,
            'invval': sheet.cell( l, 9 ).value,
            'totgst': ( sheet.cell( l, 14 ).value + sheet.cell( l, 15 ).value + sheet.cell( l, 16 ).value + sheet.cell( l, 17 ).value ),
            'itcavailable': sheet.cell( l, 20 ).value,
            'itcreason': sheet.cell( l, 21 ).value,
            'oinvno': sheet.cell( l, 1 ).value + " - " + sheet.cell( l, 0 ).value,
            'oinvdt': sheet.cell( l, 2 ).value } )

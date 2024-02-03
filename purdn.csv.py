dr = self.env['simrp.purchase'].search( [ ( 'docdate','>=',self.fromdate ), ( 'docdate','<=',self.todate ), ( 'state', 'in', [ 's', 'a' ] ) ] )
s = ""
for d in dr:
    if ( abs( d.netamount - d.matchnet ) > 0.75 ):
        s = s + d.name + ", " + d.docdate.strftime( '%d-%b-%y' ) + ", " + d.party_.name + ", " + str( d.matchnet ) + ", " + str( d.netamount ) + "\n"

self.csv = s
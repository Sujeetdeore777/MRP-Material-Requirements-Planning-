def td( title, tqty, i1, i2, i ):
    nsColor = '#ffe6cc'     # not started
    sColor = '#ff9933'      # started
    nfColor = '#99ff99'     # nearly finished
    fColor = '#33cc33'      # finished
    round2=lambda x,y=None: round(x + 0.0000000001,y)
    
    c = nsColor
    if i > 0:
        c = sColor
    if i >= tqty * 0.98:
        c = nfColor
    if i >= tqty:
        c = fColor
    
    d = '<td style="border: 2px solid black;width:8vw;background-color:' + c + ';height:8vh"><div style="position:relative; top:-2.6vh; left:0vw;">'
    d = d + '<div style="position:absolute; top: -1.0vh; left: 0.1vw; font: 1.4vh Arial;">' + title + '</div>'
    d = d + '<div style="position:absolute; top: 2.4vh; left: 1vw; width:6.5vw;  text-align:right; font: Bold 3.5vh Arial;">' + str( int( round2( i, 0 ) ) ) + '</div>'
    if i1 != 0:
        d = d + '<div style="position:absolute; top: 0.7vh; left: 0vw; font: Bold 1.8vh Arial;">' + str( int( round2( i1, 0 ) ) ) + '</div>'
    if i2 != 0:
        d = d + '<div style="position:absolute; top: -1.5vh; left: 3vw; width:4.5vw;  text-align:right; font: Bold 1.5vh Arial;">' + str( round2( i2, 2 ) ) + '</div>'
    d = d + '</div></td>'
    return d

s = "<br/><table style='color:black'><tr>"
tq = o.tqty
if len( o.wobom_s ) > 0:
    bom = o.wobom_s[ 0 ]
    s = s + td( 'Input', tq, bom.issueqty, bom.requiredqty, bom.toutput )
    if bom.toutput > tq:
        tq = bom.toutput
for p in o.woprocess_s:
    if p.planqty > tq:
        tq = p.planqty
    if p.ppokqty > tq:
        tq = p.ppokqty
    s = s + td( p.itemprocess_.shortname, tq, p.planqty, - p.pprejqty,p.ppokqty )

s = s + td( 'FG', tq, tq,o.worej,o.wook )
s = s + "</tr></table>"
self.s = s
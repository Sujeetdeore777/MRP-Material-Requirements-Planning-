def td( title, tqty, i2, i ):
    nsColor = '#FCF6ED'     # not started
    sColor = '#FAED49'      # started
    #nfColor = '#99ff99'     # nearly finished
    fColor = '#D0CCCA'      # completed
    round2=lambda x,y=None: round(x + 0.0000000001,y)
    
    c = nsColor
    if i > 0:
        c = sColor
    if i >= tqty:
        c = fColor
    #style="border: 2px solid black
    d = '<td style="border: 0.5px solid black;width:5.7vw;background-color:' + c + ';height:5.5vh"><div style="position:relative; top:-2.6vh; left:0vw">'
    d = d + '<div style="position:absolute; top: -0.1vh; left: 0.1vw; font: 1.4vh Arial">' + title + '</div>'
    d = d + '<div style="position:absolute; top: 1.2vh; left: 1vw; width:4.5vw;  text-align:right; font: Bold 3vh Arial">' + str( int( round2( i, 0 ) ) ) + '</div>'
    if i2 != 0:
        d = d + '<div style="position:absolute; top: 3.5vh; left: 0vw; font: Bold 1.5vh Arial">' + str( round2( i2, 2 ) ) + '</div>'
    d = d + '</div></td>'
    return d

s = "<br/><table style='color:black'><tr>"
tq = o.tqty
if len( o.wobom_s ) > 0:
    bom = o.wobom_s[ 0 ]
    s = s + td( 'Input', tq,  bom.requiredqty, bom.toutput )
    if bom.toutput > tq:
        tq = bom.toutput
test_dict = {}
for p in o.woprocess_s:
    test_dict[str(p.id)]= { 'seq':int(p.itemprocess_.seq), 'name':p.itemprocess_.shortname, 'tq':tq, 'rej':p.pprejqty, 'ok':p.ppokqty}
sortedlist = sorted(test_dict.items(), key=lambda x: x[1]['seq'])

for p in sortedlist:
    d1 = p[1]
    if d1['ok'] > d1['tq']:
        d1['tq'] = d1['ok']
    s = s + td( d1['name'], d1['tq'], - d1['rej'],d1['ok'] )


s = s + td( 'FG',  tq,o.worej,o.wook )
s = s + "</tr></table>"
self.s = s
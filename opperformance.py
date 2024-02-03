s = """ 
<html>
<head>
<style>
    .tr{
        background-color : #E2F516;
        font-size: 10.5px;
        text-align : center;
        font-weight : bold;
    }
    .r{
        background-color : #f6fcb6;
        border : 1;
        font-size: 12px;
        padding : 5px;
        text-align : center;
    }
</style>
</head>
"""


datadictop = json.loads( o.datadicperformance )
_logger.info("*********" +str(datadictop))

for datadict in datadictop:
    s = s + """<table border='1' style='font-size:12px;'><tr style='border:1px solid;'>
            <tr>
"""
    for opperformance in datadictop[datadict]:
        if opperformance == 'name':
            clr = '#E2F516'
            width = '5%'
        s = s + "<th class='blackhd' style='background-color:"+clr+"; height:8px; font-size:12px; border:1px solid; white-space: nowrap; '><h6 style='width:"+width+"; padding:2px; margin-top:10px;'>" +  str(opperformance).strip() + "</h6></th>"
        # s  = s + """<th class = "r">"""+ str(opperformance).strip() +"""</th>"""
    s  = s + """</tr>"""
    break



for datadict in datadictop:
    # s = s + """ <tr> """
    for op in datadictop[datadict]:
        if op == 'name':
            clr = '#D5F5E3'
        elif op == 'totalworkhours':
            clr = '#E5E7E9'
        elif op == 'workexpect':
            clr = '#E5E7E9'
        elif datadictop[datadict][op] == 0 :
            clr = '#70FCF5'
        # elif datadictop[datadict][op] >= 9 :
            # clr = 'yellow'
        elif datadictop[datadict][op] != 0 :
            clr = 'B2BABB'
        else:
            clr = '#D1F2EB'
        if datadictop[datadict][op] == 0 or datadictop[datadict][op] == '0':
            s = s + "<td style='background-color:"+clr+";border:1px solid;'> </td>"
        else:
            s = s + "<td style='background-color:"+clr+"; border:1px solid;'>" + str(datadictop[datadict][op]) + "</td>"
        # s  = s + """<td>"""+ str(datadictop[datadict][op]) +"""</td>"""
    s  = s + """<tr></tr>"""
s = s + """</table>
</div>
"""
"""
</html>
"""
o.htmltext = s
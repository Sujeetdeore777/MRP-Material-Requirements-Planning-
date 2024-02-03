datadict = json.loads(o.reporthtml)
custdict = datadict['custmaster']
_logger.info("Customer dic : " +str(custdict))

s = """
<div>
    <table style="border:1px solid;">
        <h3 class="h">Sale Order SUMMARY</h3>
            
    """
s = s + """<tr> <td>Customer Name</td>"""
for cdict in custdict:
    _logger.info("****** " +str(cdict))
    
    for cdic in custdict[cdict]:
        s = s + """<td style="border:1px solid;">"""+ str(cdic) +"""</td>"""
    break

for cdict in custdict:
    s = s + """<tr style="border:1px solid;">"""
    s = s + """<td style="border:1px solid;">"""+ str(cdict) +"""</td>"""
    
    for cdic in custdict[cdict]:
        s = s + """<td style="border:1px solid;">"""+ str(custdict[cdict][cdic]['sale']) +"""</td>"""
s = s + """</tr></table>
</div>
"""
o.reporthtml = s
# -*- coding: utf-8 -*-

{
    'name': 'SI MRP',
    'version': '1.1',
    'website': '',
    'category': 'MRP',
    'sequence': 10,
    'summary': 'Manufacturing Operations Management',
    'depends': [
        'base', 'report_xlsx', 'web', 'web_export_view', 'web_ir_actions_act_view_reload', 'web_listview_sticky_header'
    ],
    'description': "",
    'data': [
        'css.xml',
        'simrp_security.xml',
        'simrp_menu.xml',
        'simrp_sequence.xml',
        'ir.model.access.csv',
        'itemcategory.xml',
        'uom.xml',
        'item.xml',
        'itemprocess.xml',
        'party.xml',
        'processtype.xml',
        'taxscheme.xml',
        'itemrate.xml',
        'saleorder.xml',
        'dispatch.xml',
        'po.xml',
        'grnmaster.xml',
        'grn.xml',
        'qcinspection.xml',
        'stock.xml',
        'processsubcon.xml',
        'subcondc.xml',
        'accentry.xml',
        'account.xml',
        'accline.xml',
        'debit.xml',
        'purchase.xml',
        'complaint.xml',
        'credit.xml',
        'treturnabledc.xml',
        'partymaterial.xml',
        'cmdc.xml',
        'csubcondc.xml',
        'sjournal.xml',
        'fundtransaction.xml',
#        'billreference.xml',
        'indirectexpense.xml',
        'jtransaction.xml',
        'tinitinspection.xml',
        'qcidetails.xml',
        # 'tinitrejection.xml',
        'tledger.xml',
        'wo.xml',
        'r_saledc.xml',
        'r_invoice.xml',
        'r_sdc.xml',
        'closingbalance.xml',
        'r_tmdc.xml',
        'r_cmdc.xml',
        'r_po.xml',
        'employee.xml',
        'machine.xml',
        'physicalstock.xml',
        'shopio.xml',
        'woproduction.xml',
        'r_pr.xml',
        'r_itempr.xml',
        'r_pr1.xml',
        'r_prdemo.xml',
        'r_dndc.xml',
        'attendance.xml',
        'state.xml',
        'leave.xml',
                                                                                        # 'advance.xml',
        'cash.xml',
        'cashreport.xml',
        'report.xml',
        'gstr2.xml',
        'transagree.xml',
        'transporttrip.xml',
        'openingstock.xml',
        #'fundissue.xml',
        'incident.xml',
        'advgrn.xml',
        # 'tadvgrn.xml',
        'tpayable.xml',
        'r_printcheque.xml',
        'vatarget.xml',
        'salaryrecord.xml',
        'r_salaryslip.xml',
        'monthempsalary.xml',
        'paymentreceipt.xml',
        'r_tooldc.xml',
        'reportm.xml',
        'reportx_sal.xml',
        'server.xml',
        #'shift.xml',
        'sisystems.xml',
        'tdebit.xml',
#        'dummy.xml',
        'bu.xml',
        'empadvance.xml',
        'exportinv.xml',
        'auditlog.xml',
        'timport.xml',
        'tbank.xml',
        'treceivable.xml',
        'adhocbank.xml',
        'invoice.xml',
        'custsummary.xml',
        'salesummary.xml',
        'opperformancesheet.xml',
        'trans.xml',
        ],
    'qweb': ['sisystemsq.xml'],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

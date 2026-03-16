# -*- coding: utf-8 -*-
{
    'name': "Babimex Custom",
    'summary': """
        Babimex custom development  
    """,
    'description': """
        Babimex custom development
    """,
    'author': "Mainframe Monkey",
    'website': "https://www.mainframemonkey.com",
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'version': '18.0.1.0.7',
    'depends': [
        'sale'
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/res_partner_views.xml",
        "views/commercial_name_views.xml",
        "report/report_sale_order.xml",
        "report/report_invoice.xml",
        "report/report_delivery.xml",
    ],
}

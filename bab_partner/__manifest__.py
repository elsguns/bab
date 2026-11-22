# Part of the o.s.admin add-ons.
{
    'name': 'Babimex Partner',
    'version': '18.0.1.0.0',
    'category': 'Hidden',
    'summary': "Prints the customer code in the address block of quotations, invoices and delivery slips",
    'description': """
Babimex Partner
===============

Babimex customizations of how customers are shown.

Customer code in the address block: the customer address block of the
quotation / order, pro-forma invoice, invoice and delivery slip also shows the
customer code, the Reference of the company, under the customer name.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['sale', 'account', 'stock'],
    'data': [
        'views/ir_qweb_widget_templates.xml',
        'report/sale_order_templates.xml',
        'report/account_move_templates.xml',
        'report/stock_picking_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}

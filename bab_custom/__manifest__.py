# Part of the o.s.admin add-ons.
{
    'name': 'Babimex Customizations',
    'version': '18.0.1.0.0',
    'category': 'Hidden',
    'summary': "Prints the customer code in the address block of quotations, invoices and delivery slips",
    'description': """
Babimex Customizations
======================

Loose Babimex customizations that belong to no single app.

Customer code in the address block: the address blocks that ``babimex_custom``
marks with the ``babimex_commercial_name`` option (quotation / order,
pro-forma invoice, invoice and delivery slip) also show the customer code,
the Reference of the company, under the customer name.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    # babimex_custom -> sets the babimex_commercial_name option on the report address blocks
    'depends': ['babimex_custom'],
    'data': [
        'views/ir_qweb_widget_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}

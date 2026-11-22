# Part of the o.s.admin add-ons.
{
    'name': 'Babimex Reports',
    'version': '18.0.1.0.1',
    'category': 'Hidden',
    'summary': "Prints the customer code on the customer documents and the warehouse documents",
    'description': """
Babimex Reports
===============

Customer code: the Reference of the company, printed under the customer name.

* In the customer address block of the quotation / order, pro-forma invoice,
  invoice and credit note, delivery slip, picking operations and follow-up letter.
* As an extra line on the return slip and the payment receipt.
* Next to the customer on the batch transfer and on the Babimex product matrix
  slips and the product matrix per colour and customer.

The code is always the company's, also when the document is addressed to a
contact or a separate invoice or delivery address.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    # account_followup -> follow-up letter
    # stock_picking_batch -> batch transfer
    # bab_stock_delivery -> product matrix reports
    'depends': ['sale', 'account', 'account_followup', 'stock', 'stock_picking_batch', 'bab_stock_delivery'],
    'data': [
        'views/ir_qweb_widget_templates.xml',
        'report/sale_order_templates.xml',
        'report/account_move_templates.xml',
        'report/account_payment_templates.xml',
        'report/res_partner_templates.xml',
        'report/stock_picking_templates.xml',
        'report/stock_picking_batch_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}

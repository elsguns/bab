# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
{
    'name': 'Inventory: Products Sorted by Internal Reference',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Lists and reports of the Inventory app show the products in the order of their internal reference, sizes in size order",
    'description': """
Inventory: Products Sorted by Internal Reference
================================================

The lists and reports of the Inventory app show their products in the order of
the internal reference.

A variant reference often ends on its size (3L036-51-XS, 3L036-51-S, ...).
Sorted as plain text the sizes come out as L, M, S, XL, XS, XXL. When the last
part of the reference is the name of one of the variant's attribute values,
the variants of the same reference therefore follow the order of that value
instead (the order of the sizes in the attribute, as in the grid).

Where a document follows a route through the warehouse (picking operations,
batch transfer, count sheet, detailed operations), the location still comes
first and the products are sorted within each location.

Covered:

* Transfers: the operations and detailed operations, also on a batch transfer.
* On hand quantities, physical inventory, replenishment.
* The products, product variants and stock lists of the Inventory app.
* Picking operations, delivery slip, batch transfer, count sheet, and every
  printed grid built from moves or detailed operations.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['stock', 'stock_picking_batch'],
    'data': [
        'views/product_views.xml',
        'views/stock_move_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_orderpoint_views.xml',
        'views/stock_picking_batch_views.xml',
        'report/stock_report_templates.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
}

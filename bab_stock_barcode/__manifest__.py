# Part of the o.s.admin add-ons.
{
    'name': 'Barcode: Hide Untouched Lines, Block Overscan',
    'version': '18.0.1.1.0',
    'category': 'Inventory/Inventory',
    'summary': "Filter button hiding the lines nothing was scanned on yet, and an option refusing scans above the demand",
    'description': """
Barcode: Hide Untouched Lines, Block Overscan
=============================================

Two additions to the barcode app, both about keeping a large transfer readable
and correct.

Hide untouched lines
--------------------

The barcode app sorts its lines once, when the operation is opened, and then
freezes that order: a line scanned to completion turns green but keeps its
place. On a receipt of a few thousand lines it becomes hard to check what is
still unfinished.

This module adds a filter button to the barcode header. Switched on, it hides
every line nothing has been scanned on yet, so only the lines actually worked
on remain: the partially scanned ones next to the completed (green) ones. The
button is purely a display filter -- scanning, grouping and validating keep
working on the complete set of lines.

Block scanning more than demanded
---------------------------------

Standard Odoo does not stop a picker from scanning more of a product than the
transfer asked for. "Allow extra products" only refuses products that are not
on the transfer at all; a product that IS on it can be scanned without limit,
and the surplus quietly lands on an extra line. The transfer then ships more
than it should, and the goods that were meant for the next customer are gone --
whose own transfer stays waiting for stock that has already left the building.

The operation type gets a checkbox "Block scanning more than demanded". With it
on, a scan is still booked up to the demanded quantity, but the surplus is
refused with an error sound and a message naming the product. Leave it off on
receipts, where a supplier delivering more than ordered is normal.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['stock_barcode'],
    'data': [
        'views/stock_picking_type_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bab_stock_barcode/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}

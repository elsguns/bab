# Part of the o.s.admin add-ons.
{
    'name': 'Barcode: Hide Untouched Lines',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Adds a filter button in the barcode app hiding the lines nothing was scanned on yet",
    'description': """
Barcode: Hide Untouched Lines
=============================

The barcode app sorts its lines once, when the operation is opened, and then
freezes that order: a line scanned to completion turns green but keeps its
place. On a receipt of a few thousand lines it becomes hard to check what is
still unfinished.

This module adds a filter button to the barcode header. Switched on, it hides
every line nothing has been scanned on yet, so only the lines actually worked
on remain: the partially scanned ones next to the completed (green) ones. The
button is purely a display filter -- scanning, grouping and validating keep
working on the complete set of lines.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['stock_barcode'],
    'assets': {
        'web.assets_backend': [
            'bab_stock_barcode/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}

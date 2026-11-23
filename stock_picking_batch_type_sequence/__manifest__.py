# Part of the o.s.admin add-ons.
{
    'name': 'Batch Transfers: Sequence per Operation Type',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Numbers batch transfers with a sequence of their operation type",
    'description': """
Batch Transfers: Sequence per Operation Type
============================================

Odoo numbers every batch transfer from one sequence (BATCH/...), whatever the
operation type. This module adds a "Batch Sequence" on the operation type: a
new batch of that type takes its name from it (e.g. WH/BPICK/00001), so the
step of a batch shows in its name. Without one, the standard sequence is used.
Wave transfers keep their own sequence. Existing batches keep their name.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['stock_picking_batch'],
    'data': [
        'views/stock_picking_type_views.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
}

# Part of the o.s.admin add-ons.
{
    'name': 'Batch Transfers: Previous and Next Step',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Links a batch transfer to the batches of the step before and after it",
    'description': """
Batch Transfers: Previous and Next Step
=======================================

With deliveries in two or three steps, every step batches its own transfers,
and Odoo keeps no link between those batches. This module follows the chained
stock moves (pick -> pack -> ship) and shows, on every batch transfer:

* a "Previous Step" and a "Next Step" button on the form, opening the batch
  (or the list of batches) of the step before or after it;
* the same batches as two columns in the list of batch transfers.

Nothing is stored: the link is read from the moves each time.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['stock_picking_batch'],
    'data': [
        'views/stock_picking_batch_views.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
}

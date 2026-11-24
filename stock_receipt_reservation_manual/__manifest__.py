# Part of the o.s.admin add-ons.
{
    'name': 'Receipts: Manual Reservation',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Receipts no longer come in with their quantities filled in",
    'description': """
Receipts: Manual Reservation
============================

Goods coming from a vendor need no reservation, so Odoo fills in every
quantity of a receipt as soon as it is confirmed, whatever the Reservation
Method of its operation type, and the scheduler fills it in again after an
Unreserve. Whoever receives the goods then has to check every line instead of
typing what really arrived.

This module shows the Reservation Method on receipt operation types too. Set
to Manual, a receipt of that type keeps empty quantities until they are typed
in, or until Check Availability fills them all in. The other methods keep the
standard behaviour.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    'depends': ['stock'],
    'data': [],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
}

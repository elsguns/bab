# -*- coding: utf-8 -*-
{
    'name': "Website Sale: Salesperson Order on Behalf of a Customer",
    'version': '18.0.1.0.0',
    'category': 'Website/Website',
    'summary': "Let a salesperson shop on the website on behalf of one of their customers",
    'description': """
Salesperson Order on Behalf of a Customer
=========================================
A salesperson (a user in the Sales group) can pick one of their own customers
from the website shop and place an order on that customer's behalf. The order is
recorded for the selected customer, with the salesperson kept as the order's
standard Salesperson (user_id). Selecting a customer always means ordering in
that customer's name: the shop and the cart use that customer's pricelist and
fiscal position, with no way to deviate.

This is a clean reimplementation following standard Odoo conventions; it adds no
custom fields to res.partner / sale.order / account.move.

Origin
------
This module is a rewrite for Odoo 18.0 of the Odoo 19 third-party module
``shop_agents_sales_order_create``.
    """,
    'author': "",
    'license': 'LGPL-3',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
}

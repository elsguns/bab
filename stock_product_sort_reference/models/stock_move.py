# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'
    # Product before sequence: moves of a sales or purchase order carry the
    # sequence of their order line, which would keep the order of the order.
    # Every list and report that does not sort by itself follows this order,
    # also the grids built from the moves (one grid per product, in order of
    # appearance).
    _order = 'product_sort_key, sequence, id'

    product_sort_key = fields.Char(related='product_id.stock_sort_key', store=True)

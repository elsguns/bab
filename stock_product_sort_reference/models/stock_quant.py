# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_sort_key = fields.Char(related='product_id.stock_sort_key', store=True)

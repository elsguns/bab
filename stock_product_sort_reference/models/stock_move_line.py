# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    # Standard: 'result_package_id desc, id'. Packages stay first, as on the
    # delivery slip, which groups the lines per package.
    _order = 'result_package_id desc, product_sort_key, id'

    product_sort_key = fields.Char(related='product_id.stock_sort_key', store=True)

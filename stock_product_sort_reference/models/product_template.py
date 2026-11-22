# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
from odoo import api, fields, models

from .sort_key import NO_REFERENCE, to_hex


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_sort_key = fields.Char(
        compute='_compute_stock_sort_key', store=True, index=True,
        help="Technical: sorts the products of the Inventory app on their internal reference.")

    @api.depends('default_code', 'name')
    def _compute_stock_sort_key(self):
        for template in self:
            if template.default_code:
                template.stock_sort_key = to_hex(template.default_code)
            else:
                template.stock_sort_key = NO_REFERENCE + to_hex(template.with_context(lang='en_US').name)

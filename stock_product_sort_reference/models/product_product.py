# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
from odoo import api, fields, models

from .sort_key import NO_REFERENCE, SEPARATOR, to_hex


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_sort_key = fields.Char(
        compute='_compute_stock_sort_key', store=True, index=True,
        help="Technical: sorts the products of the Inventory app on their internal reference, "
             "with the variants of one reference in the order of their attribute value (the size).")

    @api.depends(
        'default_code', 'product_tmpl_id.name',
        'product_template_attribute_value_ids.product_attribute_value_id.name',
        'product_template_attribute_value_ids.product_attribute_value_id.sequence')
    def _compute_stock_sort_key(self):
        for product in self:
            code = product.default_code
            if not code:
                product.stock_sort_key = NO_REFERENCE + to_hex(product.product_tmpl_id.with_context(lang='en_US').name)
                continue
            value = product._stock_sort_reference_value()
            if value:
                prefix = code.rpartition('-')[0]
                product.stock_sort_key = '%s%s%06d' % (to_hex(prefix), SEPARATOR, max(value.sequence, 0))
            else:
                product.stock_sort_key = to_hex(code)

    def _stock_sort_reference_value(self):
        """The attribute value the reference ends on (3L036-51-XS: size XS),
        compared on the name in English, the language the values are created in.
        """
        self.ensure_one()
        prefix, dash, last_part = self.default_code.rpartition('-')
        if not dash or not prefix:
            return self.env['product.attribute.value']
        values = self.product_template_attribute_value_ids.product_attribute_value_id.with_context(lang='en_US')
        return values.filtered(lambda v: (v.name or '').strip().lower() == last_part.strip().lower())[:1]

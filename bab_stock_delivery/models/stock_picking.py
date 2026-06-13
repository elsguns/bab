# Part of the o.s.admin add-ons.
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_matrix_blocks(self):
        """Variant-matrix grids across these pickings, each paired with its picking.

        Used by the Productenmatrix report. Sorting by hoofdproduct (the product
        template shown top-left in each grid) means a BULK print over several
        deliveries groups the matrices by product instead of by customer/delivery;
        a single-delivery print just orders that delivery's matrices by product.

        Each grid is computed in its own picking's report language so a mixed-lang
        bulk print still shows each product/attribute name correctly.
        """
        blocks = []
        for picking in self:
            if not picking.sale_id:
                continue
            order = picking.sale_id.with_context(lang=picking._get_report_lang())
            for grid in order.get_report_matrixes():
                blocks.append({'picking': picking, 'grid': grid})
        # grid['header'][0]['name'] is the product template's display_name (see
        # product.template._get_template_matrix); sort on it to group by hoofdproduct.
        blocks.sort(key=lambda block: (block['grid']['header'][0]['name'] or '').lower())
        # Flag the first block of each hoofdproduct group so the report can start a
        # fresh page per product.
        previous_product = None
        for block in blocks:
            product_name = (block['grid']['header'][0]['name'] or '').lower()
            block['new_product'] = product_name != previous_product
            previous_product = product_name
        return blocks

# Part of the o.s.admin add-ons.
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_picking_orders(self):
        """All sales orders bundled in this picking.

        With stock_picking_group_by_partner_by_carrier (oca-osa) one delivery
        groups several orders per delivery address/carrier, exposed on the
        Many2many ``sale_ids`` (``sale_id`` then only holds one of them). Without
        that module ``sale_ids`` doesn't exist, so fall back on the singular
        ``sale_id`` and keep this report working stand-alone.
        """
        self.ensure_one()
        if 'sale_ids' in self._fields:
            return self.sale_ids
        return self.sale_id

    def _get_combined_matrixes(self, orders):
        """Variant matrices summed across ALL bundled orders of this picking.

        ``sale.order.get_report_matrixes`` builds one matrix per configurable
        hoofdproduct from a *single* order's lines. When a delivery groups
        several orders (see _get_picking_orders) the same hoofdproduct can occur
        in more than one order, and the user wants ONE matrix per hoofdproduct
        with the quantities added up — not a separate matrix per order.

        Every order's ``_get_matrix(template)`` returns the same skeleton for a
        given template (headers/cells come from product.template._get_template_
        matrix, which depends only on the template's attributes + company), so
        the cells line up position-by-position and we can sum their ``qty``.
        """
        self.ensure_one()
        # Only orders that actually print their grids contribute (mirrors the
        # report_grids guard inside get_report_matrixes).
        orders = orders.filtered('report_grids')
        all_lines = orders.order_line
        # Templates configured for matrix display, across the bundled orders'
        # lines (same selection as get_report_matrixes, widened to all orders).
        grid_templates = all_lines.filtered('is_configurable_product') \
            .product_template_id.filtered(lambda t: t.product_add_mode == 'matrix')

        matrixes = []
        for template in grid_templates:
            # A real grid needs more than one configured line for the template;
            # counted across the whole bundle so two orders contributing one
            # line each still produce a (summed) matrix.
            if len(all_lines.filtered(lambda line: line.product_template_id == template)) <= 1:
                continue
            combined = None
            for order in orders:
                matrix = order._get_matrix(template)
                if combined is None:
                    combined = matrix
                    continue
                # Add this order's quantities onto the running total, cell by
                # cell. Label cells (first column) have no 'qty' and are skipped.
                for row_idx, row in enumerate(matrix['matrix']):
                    for cell_idx, cell in enumerate(row):
                        if 'qty' in cell:
                            combined['matrix'][row_idx][cell_idx]['qty'] += cell.get('qty', 0)
            if combined is None:
                continue
            # Drop all-zero rows, exactly as get_report_matrixes does, but only
            # after summing so a row that is zero in one order but not another
            # survives.
            combined['matrix'] = [
                row for row in combined['matrix']
                if any(column.get('qty', 0) != 0 for column in row[1:])
            ]
            # Total ordered quantity of the hoofdproduct across this grid, shown
            # after the product name in the report header. Label cells (first
            # column) carry no 'qty' and are naturally excluded.
            combined['total_qty'] = sum(
                cell.get('qty', 0)
                for row in combined['matrix'] for cell in row if 'qty' in cell
            )
            matrixes.append(combined)
        return matrixes

    def _get_matrix_blocks(self):
        """Variant-matrix grids across these pickings, each paired with its picking.

        Used by the Productenmatrix report. Sorting by hoofdproduct (the product
        template shown top-left in each grid) means a BULK print over several
        deliveries groups the matrices by product instead of by customer/delivery;
        a single-delivery print just orders that delivery's matrices by product.

        Each grid is computed in its own picking's report language so a mixed-lang
        bulk print still shows each product/attribute name correctly. Per picking
        the matrices are summed across ALL its bundled orders (sale_ids), so a
        delivery grouping several orders shows added-up quantities per hoofdproduct.
        """
        # Only a BULK print (several deliveries at once) starts a fresh page per
        # hoofdproduct; a single-delivery print just packs its blocks back to back
        # (three to a page), so a few matrices don't waste a sheet each.
        bulk_print = len(self) > 1
        blocks = []
        for picking in self:
            orders = picking._get_picking_orders()
            if not orders:
                continue
            orders = orders.with_context(lang=picking._get_report_lang())
            for grid in picking._get_combined_matrixes(orders):
                blocks.append({'picking': picking, 'grid': grid})
        # grid['header'][0]['name'] is the product template's display_name (see
        # product.template._get_template_matrix); sort on it to group by hoofdproduct.
        blocks.sort(key=lambda block: (block['grid']['header'][0]['name'] or '').lower())
        # Flag the first block of each hoofdproduct group so a BULK print starts a
        # fresh page per product. For a single delivery new_product stays False
        # everywhere, so the report inserts no page breaks and the blocks just flow.
        previous_product = None
        for block in blocks:
            product_name = (block['grid']['header'][0]['name'] or '').lower()
            block['new_product'] = bulk_print and product_name != previous_product
            previous_product = product_name
        return blocks
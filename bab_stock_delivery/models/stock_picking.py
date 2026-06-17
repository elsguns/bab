# Part of the o.s.admin add-ons.
from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Set the first time the Productenmatrix is rendered for this picking (see
    # report.bab_stock_delivery.report_deliveryslip_matrix._get_report_values).
    # Used to warn before a reprint. copy=False so a duplicated transfer starts
    # "not yet printed".
    matrix_printed = fields.Boolean(
        string="Productenmatrix printed", default=False, copy=False, readonly=True)

    def action_print_matrix(self):
        """Print the Productenmatrix, asking to confirm a reprint.

        Entry point of the "* Productenmatrix" Action-menu server action (works on
        a single delivery and on a multi-selection from the list). For any picking
        already printed once we open a confirmation wizard instead of printing
        straight away; the wizard re-calls this with ``matrix_reprint_confirmed``
        so the second pass goes through. The outgoing-only guard lives in the
        report's _get_report_values, which also flips ``matrix_printed``.
        """
        report = self.env.ref('bab_stock_delivery.action_report_delivery_matrix')
        already_printed = self.filtered('matrix_printed')
        if already_printed and not self.env.context.get('matrix_reprint_confirmed'):
            return {
                'type': 'ir.actions.act_window',
                'name': _("Reprint Productenmatrix?"),
                'res_model': 'bab.matrix.reprint.confirm',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_picking_ids': [(6, 0, self.ids)]},
            }
        return report.report_action(self)

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

    @staticmethod
    def _line_has_ptavs(line, sorted_ptav_ids):
        """True if this order line's attribute combination matches a matrix cell.

        Mirrors the ``has_ptavs`` helper inside sale.order._get_matrix: a cell is
        identified by its sorted (no_variant + template) attribute-value ids.
        """
        ptavs = line.product_no_variant_attribute_value_ids.ids \
            + line.product_template_attribute_value_ids.ids
        ptavs.sort()
        return ptavs == sorted_ptav_ids

    def _add_order_qty_to_matrix(self, matrix, order, template):
        """Overlay one order's ordered quantities onto a prebuilt matrix skeleton.

        This is the cheap half of sale.order._get_matrix: it only does the
        cell↔line attribute matching and ADDS onto each cell's running ``qty``.
        It deliberately does NOT rebuild the skeleton (headers + cells +
        per-cell ``_is_combination_possible``), which is the expensive part of
        _get_template_matrix and is identical for every order of the template.
        Used by _get_combined_matrixes to sum a delivery's bundled orders while
        building that skeleton only once.
        """
        order_lines = order.order_line.filtered(lambda line: line.product_template_id == template)
        if not order_lines:
            return
        for row in matrix['matrix']:
            for cell in row:
                # Label cells (first column) carry a 'name' and no 'ptav_ids'.
                if cell.get('name', False):
                    continue
                lines = order_lines.filtered(lambda line: self._line_has_ptavs(line, cell['ptav_ids']))
                if lines and not lines.combo_item_id:
                    cell['qty'] += sum(lines.mapped('product_uom_qty'))

    def _get_combined_matrixes(self, orders):
        """Variant matrices summed across ALL bundled orders of this picking.

        ``sale.order.get_report_matrixes`` builds one matrix per configurable
        hoofdproduct from a *single* order's lines. When a delivery groups
        several orders (see _get_picking_orders) the same hoofdproduct can occur
        in more than one order, and the user wants ONE matrix per hoofdproduct
        with the quantities added up — not a separate matrix per order.

        Every order's ``_get_matrix(template)`` returns the same skeleton for a
        given template (headers/cells come from product.template._get_template_
        matrix, which depends only on the template's attributes + company). The
        skeleton is the expensive bit (a ``_is_combination_possible`` check per
        cell), so we build it ONCE — via the first order's _get_matrix — and then
        only overlay each remaining order's quantities (_add_order_qty_to_matrix)
        instead of rebuilding it per order. Matters for bulk prints where
        stock_picking_group_by_partner_by_carrier bundles many orders per delivery.
        """
        self.ensure_one()
        # Only orders that actually print their grids contribute (mirrors the
        # report_grids guard inside get_report_matrixes).
        orders = orders.filtered('report_grids')
        all_lines = orders.order_line
        # Every configurable product -- i.e. a product WITH variants -- gets a
        # matrix, regardless of its Sales "Variant Selection" (product_add_mode).
        # We deliberately diverge here from stock sale.order.get_report_matrixes,
        # which only grids products set to Order Grid Entry
        # (product_add_mode == 'matrix'): for this delivery slip the matrix must
        # always be built as soon as the product has variants.
        grid_templates = all_lines.filtered('is_configurable_product').product_template_id

        matrixes = []
        for template in grid_templates:
            # A real grid needs more than one configured line for the template;
            # counted across the whole bundle so two orders contributing one
            # line each still produce a (summed) matrix.
            if len(all_lines.filtered(lambda line: line.product_template_id == template)) <= 1:
                continue
            combined = None
            for order in orders:
                if combined is None:
                    # First order builds the skeleton AND fills its own quantities.
                    combined = order._get_matrix(template)
                else:
                    # Remaining orders: only add their quantities onto the skeleton.
                    self._add_order_qty_to_matrix(combined, order, template)
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
            # matrix_hide_single_value_attrs drops constant attributes (e.g.
            # material) from the row labels, see product.template.attribute.value.
            orders = orders.with_context(
                lang=picking._get_report_lang(),
                matrix_hide_single_value_attrs=True,
            )
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
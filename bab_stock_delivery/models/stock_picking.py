# Part of the o.s.admin add-ons.
from odoo import _, fields, models
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Set the first time the Productenmatrix is rendered for this picking (see
    # report.bab_stock_delivery.report_deliveryslip_matrix._get_report_values).
    # Used to warn before a reprint. copy=False so a duplicated transfer starts
    # "not yet printed" -- and so does a backorder: BAB receives and confirms per
    # product, so nearly every transfer spawns backorders, and each of those
    # carries its own goods that need their own slip.
    matrix_printed = fields.Boolean(
        string="Productenmatrix printed", default=False, copy=False, readonly=True)

    def action_print_matrix(self):
        """Print the Productenmatrix, asking to confirm a reprint.

        Entry point of the "* Productenmatrix" Action-menu server action (works on
        a single delivery and on a multi-selection from the list). For any picking
        already printed once we open a confirmation wizard instead of printing
        straight away; the wizard re-calls this with ``matrix_reprint_confirmed``
        so the second pass goes through. The guard on which transfers may be
        printed (the warehouse's pick step, done) lives in the report's
        _get_report_values, which also flips ``matrix_printed``.
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

    def _split_size_colour(self, template, ptavs):
        """Split a variant's attribute values into its size (maat) and its colour.

        The first attribute line is the size (maat) by BAB convention (see the
        T-shirt template: line 1 = Maat, line 2 = Kleur); its value is the matrix
        column, every other value forms the colour group (the matrix row).
        Returns (size_ptav, colour_ptavs) or (None, None) when the product has no
        size attribute. Shared by both matrix reports.
        """
        attribute_lines = template.valid_product_template_attribute_line_ids
        if not attribute_lines:
            return None, None
        size_ptav = ptavs.filtered(
            lambda v: v.attribute_line_id == attribute_lines[0])
        if not size_ptav:
            return None, None
        return size_ptav, ptavs - size_ptav

    def _get_reservation_matrix_blocks(self):
        """Per hoofdproduct a kleur×maat matrix of reservation figures.

        Backs the "Productenmatrix met reservaties" report. Across the selected
        transfers (``self``) it buckets every move by product template, with the
        colour (all attributes except the size) as the ROW and the size (maat --
        the first attribute line by BAB convention) as the COLUMN, so there is one
        grid per hoofdproduct just like the "* Productenmatrix" slip -- but here
        aggregated over all customers instead of the sales-order grid.

        Per template+colour+size variant it gathers, from the selected transfers'
        moves and the variant's live stock:

          * received : Σ qty already received on the purchase orders still running
          * reserved : Σ reserved qty on the selected transfers (move.quantity)
          * demand   : Σ demand qty on the selected transfers (move.product_uom_qty)
          * free     : the variant's free-to-use stock (product.product.free_qty)
          * incoming : the variant's forecasted inbound (product.product.incoming_qty)

        From these the report shows, per cell, four figures:
          0. received so far on the purchase orders still running (o, black);
          1. reserved (r, black);
          2. ONE signed figure (s) -- a shortage ``-(demand - reserved)`` (red) when
             the demand is not fully reserved, otherwise a surplus ``+free`` (green).
             Shortage and surplus never appear together: as soon as anything is
             short the surplus is suppressed, so the two are mutually exclusive by
             construction (matching "het ene is altijd 0 als het andere er is");
          3. the incoming quantity (i, blue).

        A colour (kleur) row for which nothing was received is dropped: when no
        size of that colour has an "ontvangen" (received) quantity there is no
        receipt to act on, so the row is left off the slip. This rests on the o
        figure counting every batch that came in (see below): miss one and a
        colour that IS in the warehouse silently drops off the slip.

        Only hoofdproducten with an actual reservation are listed: a block where
        nothing is reserved anywhere (e.g. make-to-order products not yet received,
        whose moves stay "waiting" with quantity 0) is dropped, since a reservation
        slip has nothing to act on for it.

        Returns one block per reserved hoofdproduct, sorted by product:
            {'template',
             'sizes': [{'name'} per size column (maat)],
             'rows':  [{'colour_name',
                        'cells': [cell-or-None per size]}]}
        where a cell is {'reserved', 'shortage', 'surplus', 'incoming'} and None
        marks a colour/size combination that is not on any selected transfer.
        """
        Ptav = self.env['product.template.attribute.value']

        # template.id -> {'template', 'sizes' (seen size ptavs), 'rows'}; each row
        # is keyed by its colour ptav ids and collects one cell per size.
        buckets = {}
        for move in self.move_ids:
            if move.state == 'cancel':
                continue
            variant = move.product_id
            template = variant.product_tmpl_id
            size_ptav, colour_ptavs = self._split_size_colour(
                template, variant.product_template_attribute_value_ids)
            if not size_ptav:
                continue
            bucket = buckets.setdefault(template.id, {
                'template': template, 'sizes': Ptav, 'rows': {}})
            bucket['sizes'] |= size_ptav
            row = bucket['rows'].setdefault(tuple(colour_ptavs.ids), {
                'colour_ptavs': colour_ptavs, 'cells': {}})
            cell = row['cells'].setdefault(size_ptav.id, {
                'variant': variant, 'reserved': 0, 'demand': 0})
            cell['reserved'] += move.quantity
            cell['demand'] += move.product_uom_qty

        # Warm the free/incoming stock caches for every variant in one batch so the
        # per-cell reads below don't each trigger a separate stock compute.
        variants = self.env['product.product'].browse(list({
            cell['variant'].id
            for b in buckets.values() for r in b['rows'].values()
            for cell in r['cells'].values()
        }))
        variants.mapped('free_qty')
        variants.mapped('incoming_qty')

        # Quantity already received of the supply that is still running ("ontvangen",
        # the o-line): NOT the last receipt in isolation, but everything that has
        # come in so far. So it pairs with the i-line: o is what arrived, i is what
        # is still to come.
        #
        # The supply is anchored on the PURCHASE ORDER, not on the move chain. A
        # chain does exist (receipt -> ... -> delivery) but it does not survive:
        # when a receipt is partially validated, stock.move._prepare_move_split_vals
        # copies only the destinations that are not done or cancelled onto the
        # backorder. A big order delivered in batches over months therefore loses
        # its links exactly for the goods that already went out -- which is the
        # history the o-line has to show. The purchase order keeps every one of its
        # receipts together regardless of what happened downstream.
        #
        # Orders that are NOT fully received count: those are the ones still being
        # delivered. A variant can sit on several of them at once (a re-order while
        # the first is still coming in) and then they add up, so a partly delivered
        # order does not drop out of sight.
        #
        # ON TOP of those comes the LAST fully received order. "Fully received"
        # means the supplier is done, not that the goods are gone: they are sitting
        # in the warehouse waiting to be handed out, which is exactly what this slip
        # is for. It is added, not used as a fallback for variants without a running
        # order -- a re-order placed while an earlier batch was still coming in
        # leaves the variant with BOTH, and then the goods that actually arrived sit
        # on the completed one while the open re-order stands at 0 received.
        # Older completed orders stay out: their goods have long been handed out.
        #
        # qty_received is the line's own "already received" figure, converted to the
        # product's UoM since the report counts in product units.
        purchase_lines = self.env['purchase.order.line'].search([
            ('product_id', 'in', variants.ids),
            ('state', 'in', ('purchase', 'done')),
        ])
        received = {}
        completed = {}
        for line in purchase_lines:
            quantity = line.product_uom._compute_quantity(
                line.qty_received, line.product_id.uom_id)
            product_id = line.product_id.id
            if float_compare(line.qty_received, line.product_qty,
                             precision_rounding=line.product_uom.rounding) < 0:
                received[product_id] = received.get(product_id, 0) + quantity
            else:
                per_order = completed.setdefault(product_id, {})
                per_order[line.order_id] = per_order.get(line.order_id, 0) + quantity

        for product_id, per_order in completed.items():
            # The last fully received order is ADDED to whatever the running orders
            # brought in, never used as a mere fallback. A variant sits on both at
            # once as soon as it is re-ordered while an earlier batch is being
            # delivered: the earlier order completes (its goods are in the
            # warehouse) while the re-order is still open at 0 received. Counting
            # only the running one then reports o = 0 for goods that are physically
            # there, reserved on the transfer and already on the briefjes -- and the
            # row rule above then drops the colour off this slip entirely.
            last_order = max(per_order, key=lambda order: (order.date_order, order.id))
            received[product_id] = received.get(product_id, 0) + per_order[last_order]

        blocks = []
        for bucket in buckets.values():
            template = bucket['template']
            # Columns: only sizes that occur on the transfers, kept in the
            # template's own size order (the size attribute's value sequence).
            size_line = template.valid_product_template_attribute_line_ids[0]
            ordered_sizes = size_line.product_template_value_ids._only_active()
            sizes = [s for s in ordered_sizes if s in bucket['sizes']]
            size_headers = [{'name': s.name} for s in sizes]
            rows = []
            for row in bucket['rows'].values():
                cells = []
                for s in sizes:
                    cell = row['cells'].get(s.id)
                    if not cell:
                        # This colour was not ordered in this size on the
                        # selected transfers -> empty matrix cell.
                        cells.append(None)
                        continue
                    reserved = cell['reserved']
                    shortage = max(cell['demand'] - reserved, 0)
                    variant = cell['variant']
                    # Surplus (free stock) only when the demand is fully reserved;
                    # while anything is short the cell shows the shortage instead,
                    # so shortage and surplus are never both non-zero.
                    surplus = variant.free_qty if not shortage else 0
                    cells.append({
                        'received': received.get(variant.id, 0),
                        'reserved': reserved,
                        'shortage': shortage,
                        'surplus': surplus if surplus > 0 else 0,
                        'incoming': variant.incoming_qty,
                    })
                # Drop a colour row for which nothing was received: when no size of
                # this kleur has an "ontvangen" quantity (received == 0 everywhere)
                # there is no receipt to act on, so the row is left off the slip.
                if not any(cell and cell['received'] for cell in cells):
                    continue
                rows.append({
                    'colour_name': ' • '.join(row['colour_ptavs'].mapped('name')),
                    'cells': cells,
                })
            # A hoofdproduct is only listed once something is actually reserved on
            # it. Make-to-order products that are not yet received cannot be
            # reserved (their moves stay "waiting" with quantity 0), so a block
            # with nothing reserved anywhere is not yet actionable on a
            # reservation slip and is dropped -- which is also why the remaining
            # blocks no longer show incoming merely echoing an ordered-but-not-
            # reserved quantity.
            if not any(cell and cell['reserved'] for row in rows for cell in row['cells']):
                continue
            rows.sort(key=lambda r: r['colour_name'].lower())
            blocks.append({
                'template': template,
                'sizes': size_headers,
                'rows': rows,
            })
        blocks.sort(key=lambda b: (b['template'].display_name or '').lower())
        return blocks

    def _get_customer_matrix_blocks(self):
        """Per hoofdproduct+kleur a customer×size matrix of ordered quantities.

        Backs the always-printable "Productenmatrix per kleur en klant" report.
        Across ALL selected delivery pickings (``self``) it buckets every variant
        order line by its product template + colour -- colour being every attribute
        except the first one, which is the size (maat) by BAB convention, see the
        T-shirt template: line 1 = Maat, line 2 = Kleur. Within each bucket the
        rows are the customers that ordered and the columns are the sizes; each
        cell holds the summed *ordered* quantity.

        Each cell carries two numbers: the *ordered* quantity (from the sales
        order) and the *reserved* quantity (from the delivery moves). They have
        different scopes on purpose. Ordered is summed per unique sales order --
        a backorder carries the same order as its origin, so iterating pickings
        would double count; we deduplicate the orders (recordset union) and read
        each order's full ordered amount once, even when only part of it sits in
        the selected pickings. Reserved is summed straight from the moves on the
        selected pickings (``self.move_ids``), so it reflects what is actually
        reserved on exactly those transfers -- letting the slip show "besteld 6 /
        gereserveerd 4". Incoming, the third number, is not customer dependent and
        lives in the size column header instead of in the cells.

        Only PARTIALLY reserved tables are emitted: this report exists to show
        what still needs attention. A product+colour table is therefore left off
        when nothing is reserved yet anywhere in it (ordered-only quantities are
        not actionable on their own) and also when everything ordered is already
        reserved (besteld == gereserveerd in every cell -- nothing left to do).

        Returns one block per (template, colour), sorted by product then colour:
            {'template', 'colour_name',
             'sizes': [{'name', 'incoming'} per size column],
             'rows': [{'customer',
                       'cells': [{'ordered', 'reserved'} per size],
                       'total_ordered', 'total_reserved'}]}
        """
        Ptav = self.env['product.template.attribute.value']

        # bucket key (template id, sorted colour ptav ids) -> aggregation
        buckets = {}

        def get_row(template, size_ptav, colour_ptavs, customer, variant):
            """Fetch (creating if needed) the customer row for a template+colour."""
            bucket = buckets.setdefault(
                (template.id, tuple(colour_ptavs.ids)), {
                    'template': template,
                    'colour_ptavs': colour_ptavs,
                    'sizes': Ptav,
                    'variants': {},
                    'rows': {},
                })
            bucket['sizes'] |= size_ptav
            # One variant per size column (this template+colour+size); used to read
            # the size's incoming quantity for the column header.
            bucket['variants'].setdefault(size_ptav.id, variant)
            return bucket['rows'].setdefault(customer.id, {
                'customer': customer, 'ordered': {}, 'reserved': {}})

        # Ordered quantities. Gathered from the sales orders behind every selected
        # picking, deduplicated (recordset union) so an order split over a pick +
        # its outgoing transfer, or over a backorder, is only counted once. We
        # deliberately do NOT restrict to outgoing transfers: the matrix must also
        # be printable from the pick step (WH/PICK) of a multi-step delivery route.
        orders = self.env['sale.order']
        for picking in self:
            orders |= picking._get_picking_orders()
        for order in orders:
            for line in order.order_line:
                if line.combo_item_id:
                    # Combo/kit child lines would double count against their parent.
                    continue
                size_ptav, colour_ptavs = self._split_size_colour(
                    line.product_template_id, line.product_template_attribute_value_ids)
                if not size_ptav:
                    continue
                row = get_row(line.product_template_id, size_ptav, colour_ptavs,
                              order.partner_id, line.product_id)
                row['ordered'][size_ptav.id] = \
                    row['ordered'].get(size_ptav.id, 0) + line.product_uom_qty

        # Reserved quantities. Straight from the moves on the selected pickings, so
        # the figure reflects what is actually reserved on exactly those transfers
        # (move.quantity is the reserved quantity on an assigned move). Each move's
        # variant gives the same size/colour split as the ordered line above.
        for move in self.move_ids:
            if move.state == 'cancel' or not move.sale_line_id:
                continue
            variant = move.product_id
            size_ptav, colour_ptavs = self._split_size_colour(
                variant.product_tmpl_id, variant.product_template_attribute_value_ids)
            if not size_ptav:
                continue
            row = get_row(variant.product_tmpl_id, size_ptav, colour_ptavs,
                          move.sale_line_id.order_id.partner_id, variant)
            row['reserved'][size_ptav.id] = \
                row['reserved'].get(size_ptav.id, 0) + move.quantity

        # Warm the incoming-qty cache for every size variant in one batch so the
        # per-size header reads below don't each trigger a separate stock compute.
        self.env['product.product'].browse(list({
            v.id for b in buckets.values() for v in b['variants'].values()
        })).mapped('incoming_qty')

        blocks = []
        for bucket in buckets.values():
            template = bucket['template']
            # Columns: only sizes that occur (ordered or reserved), but kept in the
            # template's own size order (the size attribute's value sequence). Each
            # size header also carries its incoming quantity (forecasted stock
            # coming in for that template+colour+size variant) -- not customer
            # dependent, hence in the header rather than in the cells.
            size_line = template.valid_product_template_attribute_line_ids[0]
            ordered_sizes = size_line.product_template_value_ids._only_active()
            sizes = [s for s in ordered_sizes if s in bucket['sizes']]
            size_headers = [{
                'name': s.name,
                'incoming': bucket['variants'][s.id].incoming_qty,
            } for s in sizes]
            rows = []
            for row in bucket['rows'].values():
                cells = [{
                    'ordered': row['ordered'].get(s.id, 0),
                    'reserved': row['reserved'].get(s.id, 0),
                } for s in sizes]
                rows.append({
                    'customer': row['customer'],
                    'cells': cells,
                    'total_ordered': sum(c['ordered'] for c in cells),
                    'total_reserved': sum(c['reserved'] for c in cells),
                })
            # This report only lists what still needs attention, so a product+colour
            # table is shown only when it is PARTIALLY reserved. Two cases are left
            # off: nothing reserved yet anywhere (ordered-only quantities are not
            # actionable on their own) and everything already reserved (besteld ==
            # gereserveerd in every cell -> nothing left to do). "Fully reserved"
            # mirrors the report's own green/red cells (cell ordered == reserved).
            any_reserved = any(row['total_reserved'] for row in rows)
            fully_reserved = all(
                cell['ordered'] == cell['reserved']
                for row in rows for cell in row['cells'])
            if not any_reserved or fully_reserved:
                continue
            rows.sort(key=lambda r: (r['customer'].name or '').lower())
            blocks.append({
                'template': template,
                'colour_name': ' • '.join(bucket['colour_ptavs'].mapped('name')),
                'sizes': size_headers,
                'rows': rows,
            })
        blocks.sort(key=lambda b: (
            (b['template'].display_name or '').lower(), b['colour_name'].lower()))
        return blocks

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
        # EVERY order contributes, whatever its "Print Variant Grids" setting says.
        # Stock get_report_matrixes honours that checkbox, and an earlier version
        # here did too, but this slip is a warehouse document rather than a
        # customer-facing one: the box has to be packed either way. A checkbox left
        # off on the sales order would silently drop the customer from the print
        # run, and nobody looks at that field for this purpose.
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
            # NO minimum number of order lines. Stock Odoo (and an earlier version
            # of this method) skips a template with a single line, on the grounds
            # that a one-cell grid is not a grid. That reasoning does not hold
            # here: the slip is not just a grid, it also carries the stock
            # location, the customer and the order. Drop it and the warehouse has
            # no paper saying something is waiting for that customer at all --
            # worse than a table with one box in it. Seen in the wild on S01829,
            # where 14 of the 33 hoofdproducten sit on a single line.
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
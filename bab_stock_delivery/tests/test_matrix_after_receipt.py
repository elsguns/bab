# Part of the o.s.admin add-ons.
import importlib.util
import os
import shutil
import subprocess

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMatrixAfterReceipt(TransactionCase):
    """Slips (Productenmatrix) printed when a receipt is validated.

    Two customers order two hoofdproducten (Shirt, Broek) with sizes; nothing is
    in stock, so the pick transfers wait. Receipts come in per hoofdproduct, as
    at Lucati, and every receipt must print the slips of the picks it fed,
    limited to its own hoofdproduct.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        # A pick step is needed; a database that already has one keeps it
        # (switching would fail while the packing zone holds stock).
        if cls.warehouse.delivery_steps == 'ship_only':
            cls.warehouse.delivery_steps = 'pick_ship'
        cls.receipt_type = cls.warehouse.in_type_id
        cls.pick_type = cls.warehouse.pick_type_id

        Attribute = cls.env['product.attribute']
        cls.size = Attribute.create({
            'name': 'Maat (test)',
            'value_ids': [(0, 0, {'name': 'S'}), (0, 0, {'name': 'M'})],
        })
        cls.colour = Attribute.create({
            'name': 'Kleur (test)',
            'value_ids': [(0, 0, {'name': 'Rood'})],
        })
        cls.shirt = cls._create_template('Shirt (test)')
        cls.broek = cls._create_template('Broek (test)')

        Partner = cls.env['res.partner']
        cls.customer_a = Partner.create({'name': 'Klant A (test)'})
        cls.customer_b = Partner.create({'name': 'Klant B (test)'})
        cls.order_a = cls._create_order(cls.customer_a, [
            (cls.shirt, 'S', 2), (cls.shirt, 'M', 1), (cls.broek, 'S', 1)])
        cls.order_b = cls._create_order(cls.customer_b, [(cls.shirt, 'S', 3)])
        cls.pick_a = cls.order_a.picking_ids.filtered(lambda p: p.picking_type_id == cls.pick_type)
        cls.pick_b = cls.order_b.picking_ids.filtered(lambda p: p.picking_type_id == cls.pick_type)

    @classmethod
    def _create_template(cls, name):
        return cls.env['product.template'].create({
            'name': name,
            'is_storable': True,
            # Plain make-to-stock: the database may default to MTS-O + Buy, which
            # would want a vendor. The receipts are made by hand below.
            'route_ids': [(6, 0, [])],
            'attribute_line_ids': [
                (0, 0, {'attribute_id': cls.size.id, 'value_ids': [(6, 0, cls.size.value_ids.ids)]}),
                (0, 0, {'attribute_id': cls.colour.id, 'value_ids': [(6, 0, cls.colour.value_ids.ids)]}),
            ],
        })

    @staticmethod
    def _variant(template, size):
        return template.product_variant_ids.filtered(
            lambda v: size in v.product_template_attribute_value_ids.mapped('name'))

    @classmethod
    def _create_order(cls, customer, lines):
        order = cls.env['sale.order'].create({
            'partner_id': customer.id,
            'warehouse_id': cls.warehouse.id,
            'order_line': [(0, 0, {
                'product_id': cls._variant(template, size).id,
                'product_uom_qty': qty,
            }) for template, size, qty in lines],
        })
        order.action_confirm()
        return order

    def _receive(self, lines):
        receipt = self.env['stock.picking'].create({
            'picking_type_id': self.receipt_type.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.receipt_type.default_location_dest_id.id,
            'move_ids': [(0, 0, {
                'name': template.name,
                'product_id': self._variant(template, size).id,
                'product_uom_qty': qty,
                'location_id': self.env.ref('stock.stock_location_suppliers').id,
                'location_dest_id': self.receipt_type.default_location_dest_id.id,
            }) for template, size, qty in lines],
        })
        receipt.action_confirm()
        for move in receipt.move_ids:
            move.quantity = move.product_uom_qty
        return receipt, receipt.button_validate()

    def _receive_purchase(self, lines):
        """Receipt from a purchase order, as in real life: the reservation
        overview counts what came in per purchase order (its o line)."""
        order = self.env['purchase.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Leverancier (test)'}).id,
            'picking_type_id': self.receipt_type.id,
            'order_line': [(0, 0, {
                'product_id': self._variant(template, size).id,
                'product_qty': qty,
            }) for template, size, qty in lines],
        })
        order.button_confirm()
        receipt = order.picking_ids
        for move in receipt.move_ids:
            move.quantity = move.product_uom_qty
        return receipt, receipt.button_validate()

    @staticmethod
    def _matrix_actions(action):
        if not isinstance(action, dict):
            return []
        if action.get('report_name') == 'bab_stock_delivery.report_deliveryslip_matrix':
            return [action]
        if action.get('tag') != 'do_multi_print':
            return []
        return [a for a in action['params']['reports']
                if a.get('report_name') == 'bab_stock_delivery.report_deliveryslip_matrix']

    def _receive_and_print(self, lines):
        """Receive, then print the slips as Hilde does once the reservations
        are checked; returns the receipt and the slips action."""
        receipt, action = self._receive(lines)
        self.assertFalse(self._matrix_actions(action), "no slips at validation")
        return receipt, receipt.action_print_matrix_slips()

    def _assert_downloads_slips(self, receipt, action):
        """The slips run downloads the PDF it stored on the receipt."""
        kept = receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Briefjes - '))
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], '/web/content/%s?download=true' % kept.sorted('id')[-1].id)

    def _text(self, attachments):
        """Text of the slip PDFs (real PDFs: one wkhtmltopdf run, split per pick).

        PyPDF2 1.26 shipped with Odoo 18 reads no text from wkhtmltopdf output,
        so poppler's pdftotext does it.
        """
        if not shutil.which('pdftotext'):
            self.skipTest("pdftotext (poppler-utils) is needed to read the slips")
        return ''.join(
            subprocess.run(['pdftotext', '-', '-'], input=attachment.raw,
                           capture_output=True, check=True).stdout.decode()
            for attachment in attachments
        )

    @staticmethod
    def _slips(pick):
        return pick.message_ids.attachment_ids.filtered(lambda a: a.name.endswith('.pdf'))

    def test_01_switch_off_keeps_old_behaviour(self):
        """Without the box nothing is printed and a reserved pick is refused."""
        self.receipt_type.auto_print_matrix_after_receipt = False
        receipt, action = self._receive([(self.shirt, 'S', 5), (self.shirt, 'M', 1)])
        self.assertEqual(receipt.state, 'done')
        self.assertEqual(self.pick_b.state, 'assigned', "the receipt reserves the pick")
        self.assertFalse(self._matrix_actions(action))
        self.assertFalse(self._slips(self.pick_a) | self._slips(self.pick_b))
        self.assertFalse(receipt.message_ids.attachment_ids, "nothing kept on the receipt either")
        report = self.env.ref('bab_stock_delivery.action_report_delivery_matrix')
        with self.assertRaises(UserError):
            self.env['ir.actions.report']._render_qweb_html(report, self.pick_b.ids)

    def test_02_slips_per_receipt_and_hoofdproduct(self):
        """Each receipt's slips cover the picks it fed, only for its hoofdproduct."""
        self.receipt_type.auto_print_matrix_after_receipt = True

        # Receipt 1: only Broek -> only customer A ordered it.
        receipt, action = self._receive_and_print([(self.broek, 'S', 1)])
        self._assert_downloads_slips(receipt, action)
        slips_a = self._slips(self.pick_a)
        self.assertEqual(len(slips_a), 1)
        self.assertFalse(self._slips(self.pick_b))
        html = self._text(slips_a)
        self.assertIn('Broek (test)', html)
        self.assertNotIn('Shirt (test)', html)

        # Receipt 2: Shirt -> both customers; Broek, already printed, stays off.
        receipt, action = self._receive_and_print([(self.shirt, 'S', 5), (self.shirt, 'M', 1)])
        # The receipt keeps the combined PDF with the slips of both picks.
        combined = receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Briefjes - '))
        self.assertEqual(len(combined), 1)
        text = self._text(combined)
        self.assertIn('Klant A (test)', text)
        self.assertIn('Klant B (test)', text)
        self.assertNotIn('Broek (test)', text)
        self._assert_downloads_slips(receipt, action)
        slips_a = self._slips(self.pick_a)
        self.assertEqual(len(slips_a), 2, "the earlier slip stays in the chatter")
        newest = self._text(slips_a.sorted('id')[-1])
        self.assertIn('Shirt (test)', newest)
        self.assertNotIn('Broek (test)', newest)
        text_b = self._text(self._slips(self.pick_b))
        self.assertIn('Shirt (test)', text_b)
        self.assertIn('Klant B (test)', text_b)
        self.assertNotIn('Klant A (test)', text_b, "each pick gets only its own slips")

        # The combined print renders the same filtered slips for both picks.
        report = self.env.ref('bab_stock_delivery.action_report_delivery_matrix')
        html = self.env['ir.actions.report']._render_qweb_html(
            report, (self.pick_a | self.pick_b).ids,
            data={'matrix_product_ids': self.shirt.product_variant_ids.ids})[0].decode()
        self.assertIn('Klant A (test)', html)
        self.assertIn('Klant B (test)', html)
        self.assertNotIn('Broek (test)', html)

    def test_03_partial_receipt_prints_what_is_reserved(self):
        """A short receipt only reserves part; the slip shows that part."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        # Oldest order first: A gets its 2 S, B gets the remaining 1 of 3.
        self._receive_and_print([(self.shirt, 'S', 3)])
        move_b = self.pick_b.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        self.assertEqual(move_b.quantity, 1)
        self.assertTrue(self._slips(self.pick_b))
        # A pick that got nothing from this receipt gets no slip.
        receipt, _action = self._receive_and_print([(self.broek, 'M', 1)])
        self.assertEqual(receipt.state, 'done')
        self.assertEqual(len(self._slips(self.pick_a)), 1, "nobody ordered Broek M")

    def test_04_manual_print_with_switch_on(self):
        """Hilde's own print keeps working, before and after the pick is done."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        self._receive_and_print([(self.shirt, 'S', 5), (self.shirt, 'M', 1), (self.broek, 'S', 1)])
        report = self.env.ref('bab_stock_delivery.action_report_delivery_matrix')
        # Reserved pick, full slip (both hoofdproducten, no filter).
        html = self.env['ir.actions.report']._render_qweb_html(report, self.pick_a.ids)[0].decode()
        self.assertIn('Shirt (test)', html)
        self.assertIn('Broek (test)', html)
        # Already printed by the receipt -> the reprint dialog shows first.
        action = self.pick_a.action_print_matrix()
        self.assertEqual(action.get('res_model'), 'bab.matrix.reprint.confirm')
        # Done pick still prints as before.
        self.pick_a.button_validate()
        self.assertEqual(self.pick_a.state, 'done')
        self.env['ir.actions.report']._render_qweb_html(report, self.pick_a.ids)
        # Anything that is not a pick is still refused.
        out = self.order_a.picking_ids - self.pick_a
        with self.assertRaises(UserError):
            self.env['ir.actions.report']._render_qweb_html(report, out.ids)

    def test_05_switch_only_on_receipts_form(self):
        """The box is offered on the receipt type form."""
        with Form(self.receipt_type) as form:
            form.auto_print_matrix_after_receipt = True
        self.assertTrue(self.receipt_type.auto_print_matrix_after_receipt)

    def test_06_reservations_first_then_slips(self):
        """Validating prints the reservations; the slips follow with the action."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        # Short receipt: A gets its 2 S, B only 1 of its 3 -> B shows a shortage.
        receipt, action = self._receive_purchase([(self.shirt, 'S', 3)])
        self.assertFalse(self._matrix_actions(action), "no slips at validation")
        self.assertFalse(self._slips(self.pick_a) | self._slips(self.pick_b))
        reports = [a for a in action['params']['reports']
                   if a.get('report_name') == 'bab_stock_delivery.report_reservation_matrix']
        self.assertEqual(len(reports), 1)
        self.assertEqual(set(reports[0]['context']['active_ids']), set((self.pick_a | self.pick_b).ids))
        self.assertEqual(reports[0]['data']['matrix_product_ids'], self._variant(self.shirt, 'S').ids)
        # The download without ids (see test_02) renders the overview of Shirt only.
        downloaded = self.env['ir.actions.report'].with_context(reports[0]['context'])._render_qweb_html(
            reports[0]['report_name'], None,
            data=dict(reports[0]['data'], context=reports[0]['context']))[0].decode()
        self.assertIn('Shirt (test)', downloaded)
        self.assertNotIn('Broek (test)', downloaded)
        kept = receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Reservaties - '))
        self.assertEqual(len(kept), 1, "the overview stays on the receipt")
        # The detail per colour and customer goes along in the chatter, but only
        # the overview opens.
        detail = receipt.message_ids.attachment_ids.filtered(
            lambda a: a.name.startswith('Reservaties per kleur en klant - '))
        self.assertEqual(len(detail), 1)
        self.assertEqual(detail.res_id, kept.res_id)
        self.assertNotIn('bab_stock_delivery.report_product_overview',
                         [a.get('report_name') for a in action['params']['reports']])
        text = self._text(detail)
        self.assertIn('Klant A (test)', text)
        self.assertIn('Klant B (test)', text)

        # Hilde moves the reservation of A's S to B before printing.
        move_a = self.pick_a.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        move_b = self.pick_b.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        move_a.quantity = 0
        move_b.quantity = 3
        action = receipt.action_print_matrix_slips()
        self._assert_downloads_slips(receipt, action)
        self.assertTrue(self._slips(self.pick_b), "only the pick that holds stock now")
        self.assertFalse(self._slips(self.pick_a))

    def test_07_slips_action_refuses_other_transfers(self):
        self.receipt_type.auto_print_matrix_after_receipt = True
        with self.assertRaises(UserError):
            self.pick_a.action_print_matrix_slips()
        # A receipt that reserved nothing (nobody ordered Broek M) still prints:
        # an empty PDF, and the receipt counts as printed.
        receipt, _action = self._receive([(self.broek, 'M', 1)])
        # As from the gear menu: the server action runs with the receipt as active_ids.
        action = receipt.with_context(active_ids=receipt.ids).action_print_matrix_slips()
        # The download is the stored empty PDF, not a report action that would
        # render the receipt itself and refuse it ("not a pick transfer").
        self._assert_downloads_slips(receipt, action)
        self.assertIn('Geen pickbon heeft iets gereserveerd', self._text(
            receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Briefjes - '))))
        self.assertTrue(receipt.matrix_printed)
        kept = receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Briefjes - '))
        self.assertEqual(len(kept), 1)

    def test_08_receipt_remembers_its_slips(self):
        """A receipt shows under "Slips to print" until its slips are printed;
        a second run without any change has nothing to print."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        count_before = self.receipt_type.count_matrix_slips_to_print
        receipt, _action = self._receive([(self.shirt, 'S', 5)])
        self.assertFalse(receipt.matrix_printed)
        self.receipt_type.invalidate_recordset(['count_matrix_slips_to_print'])
        self.assertEqual(self.receipt_type.count_matrix_slips_to_print, count_before + 1)
        overview = self.receipt_type.get_action_matrix_slips_to_print()
        self.assertIn(receipt, self.env['stock.picking'].search(overview['domain']))

        action = receipt.action_print_matrix_slips()
        self._assert_downloads_slips(receipt, action)
        self.assertTrue(receipt.matrix_printed)
        self.receipt_type.invalidate_recordset(['count_matrix_slips_to_print'])
        self.assertEqual(self.receipt_type.count_matrix_slips_to_print, count_before)
        self.assertNotIn(receipt, self.env['stock.picking'].search(overview['domain']))

        # Second time without any change: nothing to print, the PDF is on the receipt.
        slips_before = len(self._slips(self.pick_a))
        with self.assertRaises(UserError):
            receipt.action_print_matrix_slips()
        self.assertEqual(len(self._slips(self.pick_a)), slips_before)

    def test_09_receipt_without_open_picks_waits_for_hilde(self):
        """Nobody waits for what came in: the receipt still shows under "Slips
        to print" until Hilde runs the slips, which then prints an empty PDF."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        other = self._create_template('Jas (test)')
        count_before = self.receipt_type.count_matrix_slips_to_print
        receipt, _action = self._receive([(other, 'S', 1)])
        self.assertFalse(receipt.matrix_printed)
        self.receipt_type.invalidate_recordset(['count_matrix_slips_to_print'])
        self.assertEqual(self.receipt_type.count_matrix_slips_to_print, count_before + 1)
        receipt.action_print_matrix_slips()
        self.assertTrue(receipt.matrix_printed)
        self.receipt_type.invalidate_recordset(['count_matrix_slips_to_print'])
        self.assertEqual(self.receipt_type.count_matrix_slips_to_print, count_before)

    def test_10_delivery_reprint_dialog_unchanged(self):
        """The dialog of the Productenmatrix on a pick keeps printing that."""
        self.pick_a.matrix_printed = True
        action = self.pick_a.action_print_matrix()
        wizard = self.env['bab.matrix.reprint.confirm'].with_context(action['context']).create({})
        self.assertEqual(wizard.print_method, 'matrix')

    def test_11_gear_menu_shows_the_fitting_slip_action(self):
        """Each transfer hides the slip action that does not fit it."""
        pick_action = self.env.ref('bab_stock_delivery.action_print_matrix_server')
        receipt_action = self.env.ref('bab_stock_delivery.action_print_matrix_slips_server')
        self.receipt_type.auto_print_matrix_after_receipt = True
        self.assertEqual(self.pick_a.matrix_hidden_action_ids, [receipt_action.id])
        receipt, _action = self._receive([(self.shirt, 'S', 1)])
        self.assertEqual(receipt.matrix_hidden_action_ids, [pick_action.id])
        # Any other transfer (here a delivery): neither action.
        delivery = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        self.assertEqual(sorted(delivery.matrix_hidden_action_ids), sorted([pick_action.id, receipt_action.id]))
        # A receipt type that does not print the slips: neither action.
        self.receipt_type.auto_print_matrix_after_receipt = False
        receipt.invalidate_recordset(['matrix_hidden_action_ids'])
        self.assertEqual(sorted(receipt.matrix_hidden_action_ids), sorted([pick_action.id, receipt_action.id]))

    def test_12_reservation_reports_printed_on_a_receipt(self):
        """Both reservation reports printed on a receipt cover its open picks."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        # A gets its 2 S, B only 1 of its 3: partially reserved, so the detail
        # per colour and customer shows the table.
        receipt, _action = self._receive_purchase([(self.shirt, 'S', 3)])
        Report = self.env['ir.actions.report']
        for report_name in ('bab_stock_delivery.report_reservation_matrix',
                            'bab_stock_delivery.report_product_overview'):
            html = Report._render_qweb_html(report_name, receipt.ids)[0].decode()
            self.assertIn('Shirt (test)', html, report_name)
            self.assertNotIn('Broek (test)', html, "only the received hoofdproducten")
        detail = Report._render_qweb_html(
            'bab_stock_delivery.report_product_overview', receipt.ids)[0].decode()
        self.assertIn('Klant A (test)', detail)
        self.assertIn('Klant B (test)', detail)
        # Picks, or receipts mixed with other transfers, are printed as selected.
        self.assertEqual(self.pick_a._get_matrix_report_pickings(), self.pick_a)
        self.assertFalse(self.pick_a._get_matrix_report_pickings().env.context.get('matrix_product_ids'))
        self.assertEqual((receipt | self.pick_a)._get_matrix_report_pickings(), receipt | self.pick_a)

    def test_13_only_the_received_variants(self):
        """After a receipt the reports and slips cover the received variants only.

        Shirt S comes in, Shirt M (ordered by A) does not: M stays off the
        reservation overview, the detail per colour and customer, and the slip.
        """
        self.receipt_type.auto_print_matrix_after_receipt = True
        receipt, _action = self._receive_purchase([(self.shirt, 'S', 5)])
        picks = receipt._get_matrix_report_pickings()
        self.assertEqual(picks.env.context['matrix_product_ids'], self._variant(self.shirt, 'S').ids)
        self.assertEqual(picks, self.pick_a | self.pick_b, "Broek alone would not feed a pick")

        blocks = picks._get_reservation_matrix_blocks()
        self.assertEqual([size['name'] for size in blocks[0]['sizes']], ['S'])

        # A pick printed without the filter still shows both sizes.
        blocks = self.pick_a._get_reservation_matrix_blocks()
        self.assertEqual(sorted(size['name'] for size in blocks[0]['sizes']), ['M', 'S'])

        # Slip of A: only its 2 S, not its 1 M.
        orders = self.pick_a._get_picking_orders()
        grids = self.pick_a.with_context(
            matrix_product_ids=self._variant(self.shirt, 'S').ids)._get_combined_matrixes(orders)
        self.assertEqual([grid['total_qty'] for grid in grids], [2])
        grids = self.pick_a._get_combined_matrixes(orders)
        self.assertEqual(sorted(grid['total_qty'] for grid in grids), [1, 3], "Broek 1, Shirt 2 S + 1 M")

    def test_14_detail_from_a_receipt_keeps_fully_reserved(self):
        """Printed from a receipt the detail shows the spread, even when complete."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        # 5 S covers A's 2 and B's 3: fully reserved.
        receipt, _action = self._receive_purchase([(self.shirt, 'S', 5)])
        blocks = receipt._get_matrix_report_pickings()._get_customer_matrix_blocks()
        self.assertEqual(len(blocks), 1)
        reserved = {row['customer'].name: row['total_reserved'] for row in blocks[0]['rows']}
        self.assertEqual(reserved, {'Klant A (test)': 2, 'Klant B (test)': 3})

    def test_15_slip_prints_only_the_received_variants(self):
        """A variant reserved from earlier stock stays off the slip of this receipt."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        self._receive([(self.shirt, 'M', 1)])
        receipt, _action = self._receive([(self.shirt, 'S', 5)])
        receipt.action_print_matrix_slips()
        text = self._text(self._slips(self.pick_a).sorted('id')[-1])
        self.assertIn('2 stuks', text, "A: its 2 S, not its M reserved by the first receipt")

    def test_16_second_receipt_prints_only_what_it_added(self):
        """Two receipts of the same variant: the second slip shows its own part."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        # First 1 S: A (oldest order) gets it.
        self._receive_and_print([(self.shirt, 'S', 1)])
        move_a = self.pick_a.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        self.assertEqual((move_a.quantity, move_a.matrix_printed_qty), (1, 1))
        # Then 4 S: A gets its 2nd, B its 3.
        self._receive_and_print([(self.shirt, 'S', 4)])
        self.assertEqual(move_a.matrix_printed_qty, 2)
        text_a = self._text(self._slips(self.pick_a).sorted('id')[-1])
        self.assertIn('1 stuks', text_a, "A: only the one added by the 2nd receipt")
        self.assertNotIn('Vervangt', text_a)
        text_b = self._text(self._slips(self.pick_b).sorted('id')[-1])
        self.assertIn('3 stuks', text_b)

    def test_17_moved_reservation_replaces_the_slip(self):
        """A reservation moved after the slips: new full slip for the one who lost,
        the difference for the one who gained."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        receipt, _action = self._receive_and_print([(self.shirt, 'S', 5)])
        variant = self._variant(self.shirt, 'S')
        move_a = self.pick_a.move_ids.filtered(lambda m: m.product_id == variant)
        move_b = self.pick_b.move_ids.filtered(lambda m: m.product_id == variant)
        self.assertEqual((move_a.matrix_printed_qty, move_b.matrix_printed_qty), (2, 3))
        # One S moves from B to A: B 2, A 3 (A ordered 2, so over-reserve is
        # allowed by quantity on the move here).
        move_b.quantity = 2
        move_a.quantity = 3
        slips_a, slips_b = len(self._slips(self.pick_a)), len(self._slips(self.pick_b))
        receipt.action_print_matrix_slips()
        text_b = self._text(self._slips(self.pick_b).sorted('id')[-1])
        self.assertIn('Vervangt het vorige briefje', text_b)
        self.assertIn('2 stuks', text_b, "B: the full reservation now")
        text_a = self._text(self._slips(self.pick_a).sorted('id')[-1])
        self.assertNotIn('Vervangt', text_a)
        self.assertIn('1 stuks', text_a, "A: only the one it gained")
        self.assertEqual((len(self._slips(self.pick_a)), len(self._slips(self.pick_b))), (slips_a + 1, slips_b + 1))
        self.assertEqual((move_a.matrix_printed_qty, move_b.matrix_printed_qty), (3, 2))

    def test_18_manual_slip_counts_as_printed(self):
        """The full slip printed from the pick puts its reservation on paper."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        self._receive([(self.shirt, 'S', 2)])
        report = self.env.ref('bab_stock_delivery.action_report_delivery_matrix')
        self.env['ir.actions.report']._render_qweb_html(report, self.pick_a.ids)
        move_a = self.pick_a.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        self.assertEqual(move_a.matrix_printed_qty, 2)

    def test_19_overview_of_a_receipt_shows_only_that_receipt(self):
        """Second receipt of a variant: o is what it brought, r how much of it was
        reserved, slips printed or not."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        self._receive([(self.shirt, 'S', 2)])  # A's 2 S, no slips printed
        receipt, _action = self._receive_purchase([(self.shirt, 'S', 1)])  # B gets 1
        self.assertEqual(receipt.move_ids.matrix_reserved_qty, 1)
        blocks = receipt._get_matrix_report_pickings()._get_reservation_matrix_blocks()
        cell = blocks[0]['rows'][0]['cells'][0]
        self.assertEqual((cell['received'], cell['reserved']), (1, 1))
        self.assertEqual(cell['shortage'], 2, "B still short 2 of its 3: the total stays")
        # From the picks themselves: everything, as before.
        blocks = (self.pick_a | self.pick_b)._get_reservation_matrix_blocks()
        self.assertEqual(blocks[0]['rows'][0]['cells'][0]['reserved'], 3)
        # More than anyone waits for: only the part that was reserved.
        extra, _action = self._receive([(self.shirt, 'S', 5)])  # B's last 2
        self.assertEqual(extra.move_ids.matrix_reserved_qty, 2)

    def test_20_backorder_chain_prints_once(self):
        """Receipt, backorder, backorder of the backorder: the slips of the last
        one carry everything, the earlier ones leave "Slips to print"."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        receipt, _action = self._receive([(self.shirt, 'S', 1)])
        receipt2, _action = self._receive([(self.shirt, 'S', 1)])
        receipt2.backorder_id = receipt
        receipt3, _action = self._receive([(self.shirt, 'S', 3)])
        receipt3.backorder_id = receipt2
        receipt3.action_print_matrix_slips()
        self.assertTrue(receipt3.matrix_printed)
        self.assertTrue(receipt.matrix_printed, "printed with the last backorder")
        self.assertTrue(receipt2.matrix_printed)
        self.assertIn('WH/IN', receipt.message_ids[0].body)

    def test_21_already_on_other_slips_is_no_empty_pdf(self):
        """A receipt whose reservations went on another receipt's slips gets a
        notice, not the empty "nothing reserved" PDF."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        first, _action = self._receive([(self.shirt, 'S', 1)])
        second, _action = self._receive([(self.shirt, 'S', 1)])
        second.action_print_matrix_slips()
        action = first.action_print_matrix_slips()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertTrue(first.matrix_printed)
        self.assertFalse(first.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Briefjes - ')))

    def test_22_smart_button_pick_batches(self):
        """The receipt opens the open pick batches that reserved what it brought."""
        batch = self.env['stock.picking.batch'].create({
            'picking_type_id': self.pick_type.id,
            'picking_ids': [(6, 0, self.pick_a.ids)],
        })
        batch.action_confirm()
        receipt, _action = self._receive([(self.shirt, 'S', 1)])  # A, oldest order
        self.assertEqual(receipt.matrix_pick_batch_count, 1)
        action = receipt.action_open_matrix_pick_batches()
        self.assertEqual(action['res_id'], batch.id)
        other, _action = self._receive([(self.broek, 'M', 1)])  # nobody ordered it
        self.assertEqual(other.matrix_pick_batch_count, 0)

    def test_23_detail_of_a_receipt_leaves_picked_goods_off(self):
        """From a receipt the detail counts what is still to pick, not what a done
        pick already moved on."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        receipt, _action = self._receive([(self.shirt, 'S', 2), (self.shirt, 'M', 1)])  # A complete
        self.pick_a.move_ids.filtered(lambda m: m.product_id.product_tmpl_id == self.shirt).picked = True
        self.pick_a._action_done()
        blocks = receipt._get_matrix_report_pickings()._get_customer_matrix_blocks()
        customers = [row['customer'] for block in blocks for row in block['rows']]
        self.assertNotIn(self.customer_a, customers, "A's shirts went on to the next step")

    def _run_migration_1_12(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'migrations', '18.0.1.12.0', 'post-migrate.py')
        spec = importlib.util.spec_from_file_location('bab_migrate_1_12', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.env.flush_all()
        module.migrate(self.env.cr, '18.0.1.11.0')
        self.env.invalidate_all()

    def test_24_migration_keeps_pending_slips(self):
        """The 1.12.0 migration only counts as printed what really went on slips:
        a receipt still waiting for its slips keeps them, and a database whose
        receipts do not print the slips (Vasa) is left alone."""
        pick_moves = (self.pick_a | self.pick_b).move_ids
        # Vasa: nothing on paper before a pick is done.
        vasa_receipt, _action = self._receive([(self.shirt, 'S', 5)])
        pick_moves.matrix_printed_qty = 0
        self._run_migration_1_12()
        self.assertFalse(any(pick_moves.mapped('matrix_printed_qty')))
        # As the 1.4.0 migration does for receipts done before the box existed.
        vasa_receipt.matrix_printed = True

        # Lucati: Shirt's slips were printed, Broek's receipt still waits.
        self.receipt_type.auto_print_matrix_after_receipt = True
        shirt_receipt, _action = self._receive([(self.shirt, 'M', 1)])
        shirt_receipt.action_print_matrix_slips()
        self._receive([(self.broek, 'S', 1)])
        pick_moves.matrix_printed_qty = 0
        self._run_migration_1_12()
        shirt_moves = pick_moves.filtered(lambda m: m.product_id.product_tmpl_id == self.shirt and m.quantity)
        broek_moves = pick_moves.filtered(lambda m: m.product_id.product_tmpl_id == self.broek and m.quantity)
        self.assertTrue(shirt_moves and broek_moves)
        for move in shirt_moves:
            self.assertEqual(move.matrix_printed_qty, move.quantity)
        self.assertFalse(any(broek_moves.mapped('matrix_printed_qty')), "Broek's slips still to print")

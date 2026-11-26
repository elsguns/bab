# Part of the o.s.admin add-ons.
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
        _receipt, action = self._receive_and_print([(self.broek, 'S', 1)])
        actions = self._matrix_actions(action)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['context']['active_ids'], self.pick_a.ids)
        self.assertEqual(actions[0]['data']['matrix_template_ids'], self.broek.ids)
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
        actions = self._matrix_actions(action)
        self.assertEqual(len(actions), 1)
        self.assertEqual(set(actions[0]['context']['active_ids']), set((self.pick_a | self.pick_b).ids))
        self.assertEqual(actions[0]['data']['matrix_template_ids'], self.shirt.ids)
        # The download in the browser: the web client puts the data in the URL
        # and the picks only in the context, no ids (see getReportUrl).
        downloaded = self.env['ir.actions.report'].with_context(actions[0]['context'])._render_qweb_html(
            actions[0]['report_name'], None,
            data=dict(actions[0]['data'], context=actions[0]['context']))[0].decode()
        self.assertIn('Klant A (test)', downloaded)
        self.assertIn('Klant B (test)', downloaded)
        self.assertNotIn('Broek (test)', downloaded)
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
            data={'matrix_template_ids': self.shirt.ids})[0].decode()
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
        self.assertEqual(reports[0]['data']['matrix_template_ids'], self.shirt.ids)
        # The download without ids (see test_02) renders the overview of Shirt only.
        downloaded = self.env['ir.actions.report'].with_context(reports[0]['context'])._render_qweb_html(
            reports[0]['report_name'], None,
            data=dict(reports[0]['data'], context=reports[0]['context']))[0].decode()
        self.assertIn('Shirt (test)', downloaded)
        self.assertNotIn('Broek (test)', downloaded)
        kept = receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Reservaties - '))
        self.assertEqual(len(kept), 1, "the overview stays on the receipt")

        # Hilde moves the reservation of A's S to B before printing.
        move_a = self.pick_a.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        move_b = self.pick_b.move_ids.filtered(lambda m: m.product_id == self._variant(self.shirt, 'S'))
        move_a.quantity = 0
        move_b.quantity = 3
        action = receipt.action_print_matrix_slips()
        self.assertEqual(action['report_name'], 'bab_stock_delivery.report_deliveryslip_matrix')
        self.assertEqual(action['context']['active_ids'], self.pick_b.ids, "only the pick that holds stock now")
        self.assertTrue(self._slips(self.pick_b))
        self.assertFalse(self._slips(self.pick_a))

    def test_07_slips_action_refuses_other_transfers(self):
        self.receipt_type.auto_print_matrix_after_receipt = True
        with self.assertRaises(UserError):
            self.pick_a.action_print_matrix_slips()
        # A receipt that reserved nothing (nobody ordered Broek M) still prints:
        # an empty PDF, and the receipt counts as printed.
        receipt, _action = self._receive([(self.broek, 'M', 1)])
        action = receipt.action_print_matrix_slips()
        self.assertEqual(action['report_name'], 'bab_stock_delivery.report_deliveryslip_matrix')
        self.assertFalse(action['context'].get('active_ids'))
        # The download (no ids, as in test_02) renders the empty slips page.
        downloaded = self.env['ir.actions.report'].with_context(action['context'])._render_qweb_html(
            action['report_name'], None, data=dict(action['data'], context=action['context']))[0].decode()
        self.assertIn('Geen pickbon heeft iets gereserveerd', downloaded)
        self.assertTrue(receipt.matrix_printed)
        kept = receipt.message_ids.attachment_ids.filtered(lambda a: a.name.startswith('Briefjes - '))
        self.assertEqual(len(kept), 1)

    def test_08_receipt_remembers_its_slips(self):
        """A receipt shows under "Slips to print" until its slips are printed;
        printing them again asks first."""
        self.receipt_type.auto_print_matrix_after_receipt = True
        count_before = self.receipt_type.count_matrix_slips_to_print
        receipt, _action = self._receive([(self.shirt, 'S', 5)])
        self.assertFalse(receipt.matrix_printed)
        self.receipt_type.invalidate_recordset(['count_matrix_slips_to_print'])
        self.assertEqual(self.receipt_type.count_matrix_slips_to_print, count_before + 1)
        overview = self.receipt_type.get_action_matrix_slips_to_print()
        self.assertIn(receipt, self.env['stock.picking'].search(overview['domain']))

        action = receipt.action_print_matrix_slips()
        self.assertEqual(action['report_name'], 'bab_stock_delivery.report_deliveryslip_matrix')
        self.assertTrue(receipt.matrix_printed)
        self.receipt_type.invalidate_recordset(['count_matrix_slips_to_print'])
        self.assertEqual(self.receipt_type.count_matrix_slips_to_print, count_before)
        self.assertNotIn(receipt, self.env['stock.picking'].search(overview['domain']))

        # Second time: the dialog, which then prints again or skips.
        action = receipt.action_print_matrix_slips()
        self.assertEqual(action['res_model'], 'bab.matrix.reprint.confirm')
        wizard = self.env['bab.matrix.reprint.confirm'].with_context(action['context']).create({})
        self.assertEqual(wizard.print_method, 'slips')
        self.assertEqual(wizard.already_printed_ids, receipt)
        slips_before = len(self._slips(self.pick_a))
        action = wizard.action_confirm()
        self.assertEqual(action['report_name'], 'bab_stock_delivery.report_deliveryslip_matrix')
        self.assertTrue(action['close_on_report_download'])
        self.assertEqual(len(self._slips(self.pick_a)), slips_before + 1, "printed again")
        self.assertEqual(wizard.action_skip_reprints(), {'type': 'ir.actions.act_window_close'})

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

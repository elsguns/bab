# Part of the o.s.admin add-ons.
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestReceiptReservationManual(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.receipt_type = cls.warehouse.in_type_id
        cls.out_type = cls.warehouse.out_type_id
        cls.vendor_location = cls.env.ref('stock.stock_location_suppliers')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.product = cls.env['product.product'].create({'name': 'Manual receipt (test)', 'is_storable': True})
        cls.partner = cls.env['res.partner'].create({'name': 'Vendor (test)'})

    def _picking(self, picking_type, src, dest, qty):
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id, 'partner_id': self.partner.id,
            'location_id': src.id, 'location_dest_id': dest.id,
            'move_ids': [(0, 0, {
                'name': self.product.name, 'product_id': self.product.id, 'product_uom_qty': qty,
                'product_uom': self.product.uom_id.id, 'location_id': src.id, 'location_dest_id': dest.id,
            })],
        })
        picking.action_confirm()
        return picking

    def _receipt(self, qty=10):
        return self._picking(self.receipt_type, self.vendor_location, self.stock_location, qty)

    def test_standard_receipt_filled_in(self):
        self.receipt_type.reservation_method = 'at_confirm'
        receipt = self._receipt()
        self.assertEqual(receipt.state, 'assigned')
        self.assertEqual(receipt.move_ids.quantity, 10)

    def test_manual_receipt_stays_empty(self):
        self.receipt_type.reservation_method = 'manual'
        receipt = self._receipt()
        self.assertEqual(receipt.move_ids.quantity, 0)
        self.assertEqual(receipt.move_ids.state, 'confirmed')
        # Standard Odoo shows a receipt from a vendor as Ready anyway, so it stays in the same list.
        self.assertEqual(receipt.state, 'assigned')
        self.assertTrue(receipt.show_check_availability)
        # The scheduler does not fill it in either.
        self.env['procurement.group'].run_scheduler()
        self.assertEqual(receipt.move_ids.quantity, 0)

    def test_manual_receipt_typed_in_and_validated(self):
        self.receipt_type.reservation_method = 'manual'
        receipt = self._receipt()
        receipt.move_ids.write({'quantity': 7, 'picked': True})
        receipt.with_context(cancel_backorder=False)._action_done()
        self.assertEqual(receipt.state, 'done')
        self.assertEqual(self.product.qty_available, 7)
        backorder = receipt.backorder_ids
        self.assertEqual(backorder.move_ids.product_uom_qty, 3)
        self.assertEqual(backorder.move_ids.quantity, 0, "the backorder stays empty as well")

    def test_check_availability_fills_in(self):
        self.receipt_type.reservation_method = 'manual'
        receipt = self._receipt()
        receipt.action_assign()
        self.assertEqual(receipt.state, 'assigned')
        self.assertEqual(receipt.move_ids.quantity, 10)

    def test_delivery_still_reserved(self):
        """Outgoing transfers keep reserving: the received stock goes to the waiting delivery."""
        self.receipt_type.reservation_method = 'manual'
        delivery = self._picking(self.out_type, self.stock_location, self.customer_location, 4)
        self.assertEqual(delivery.state, 'confirmed')
        receipt = self._receipt()
        receipt.move_ids.write({'quantity': 10, 'picked': True})
        receipt._action_done()
        self.assertEqual(delivery.state, 'assigned')
        self.assertEqual(delivery.move_ids.quantity, 4)

    def test_method_shown_on_receipts(self):
        self.assertFalse(self.receipt_type.hide_reservation_method)

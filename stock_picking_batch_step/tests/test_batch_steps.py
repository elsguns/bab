# Part of the o.s.admin add-ons.
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestBatchSteps(TransactionCase):
    """Previous/next step batches, read through the chained stock moves."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.pick_type = cls.warehouse.pick_type_id
        cls.out_type = cls.warehouse.out_type_id
        # The batches are made by hand below; keep the automatic ones out.
        (cls.pick_type | cls.out_type).auto_batch = False
        cls.product = cls.env['product.product'].create({'name': 'Steps (test)', 'is_storable': True})
        cls.customer = cls.env['res.partner'].create({'name': 'Customer Steps (test)'})
        cls.output = cls.env['stock.location'].create({
            'name': 'Output (test)', 'location_id': cls.warehouse.view_location_id.id})

    def _chain(self):
        """A pick transfer whose move feeds the move of a delivery."""
        Picking = self.env['stock.picking']
        ship = Picking.create({
            'picking_type_id': self.out_type.id,
            'partner_id': self.customer.id,
            'location_id': self.output.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_ids': [(0, 0, {
                'name': self.product.name, 'product_id': self.product.id, 'product_uom_qty': 1,
                'location_id': self.output.id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            })],
        })
        pick = Picking.create({
            'picking_type_id': self.pick_type.id,
            'partner_id': self.customer.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.output.id,
            'move_ids': [(0, 0, {
                'name': self.product.name, 'product_id': self.product.id, 'product_uom_qty': 1,
                'location_id': self.warehouse.lot_stock_id.id, 'location_dest_id': self.output.id,
                'move_dest_ids': [(4, ship.move_ids.id)],
            })],
        })
        return pick, ship

    def test_two_picks_into_one_ship_batch(self):
        Batch = self.env['stock.picking.batch']
        pick_1, ship_1 = self._chain()
        pick_2, ship_2 = self._chain()
        pick_batch_1 = Batch.create({'picking_ids': [(6, 0, pick_1.ids)]})
        pick_batch_2 = Batch.create({'picking_ids': [(6, 0, pick_2.ids)]})
        ship_batch = Batch.create({'picking_ids': [(6, 0, (ship_1 | ship_2).ids)]})

        self.assertEqual(ship_batch.previous_batch_ids, pick_batch_1 | pick_batch_2)
        self.assertEqual(ship_batch.previous_batch_count, 2)
        self.assertFalse(ship_batch.next_batch_ids)
        self.assertEqual(pick_batch_1.next_batch_ids, ship_batch)
        self.assertFalse(pick_batch_1.previous_batch_ids)

        action = pick_batch_1.action_view_next_batches()
        self.assertEqual(action['res_id'], ship_batch.id)
        action = ship_batch.action_view_previous_batches()
        self.assertEqual(action['domain'], [('id', 'in', (pick_batch_1 | pick_batch_2).ids)])
        # A saved default filter (e.g. only open batches) must not hide them.
        self.assertTrue(action['context'].get('search_disable_custom_filters'))

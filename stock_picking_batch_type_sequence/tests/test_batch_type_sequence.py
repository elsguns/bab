# Part of the o.s.admin add-ons.
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestBatchTypeSequence(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.pick_type = warehouse.pick_type_id
        cls.out_type = warehouse.out_type_id
        cls.pick_type.batch_sequence_id = cls.env['ir.sequence'].create({
            'name': 'Batch Pick (test)', 'prefix': 'TBPICK/', 'padding': 4,
            'company_id': cls.env.company.id,
        })
        cls.out_type.batch_sequence_id = False

    def test_type_sequence(self):
        Batch = self.env['stock.picking.batch']
        first, second = Batch.create([{'picking_type_id': self.pick_type.id} for _i in range(2)])
        self.assertEqual(first.name, 'TBPICK/0001')
        self.assertEqual(second.name, 'TBPICK/0002')

    def test_standard_sequence(self):
        """No sequence on the type, no type, or a wave: the standard names."""
        Batch = self.env['stock.picking.batch']
        self.assertFalse(Batch.create({'picking_type_id': self.out_type.id}).name.startswith('TBPICK/'))
        self.assertFalse(Batch.create({}).name.startswith('TBPICK/'))
        wave = Batch.create({'picking_type_id': self.pick_type.id, 'is_wave': True})
        self.assertFalse(wave.name.startswith('TBPICK/'))

    def test_given_name_kept(self):
        batch = self.env['stock.picking.batch'].create({'picking_type_id': self.pick_type.id, 'name': 'OWN'})
        self.assertEqual(batch.name, 'OWN')

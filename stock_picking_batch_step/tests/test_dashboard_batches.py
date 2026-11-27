# Part of the o.s.admin add-ons.
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDashboardBatches(TransactionCase):

    def test_dashboard_action_skips_default_favorite(self):
        picking_type = self.env.ref('stock.picking_type_out')
        context = picking_type.action_batch()['context']
        self.assertTrue(context['search_disable_custom_filters'])
        self.assertEqual(context['search_default_picking_type_id'], picking_type.id)
        self.assertTrue(context['search_default_draft'])

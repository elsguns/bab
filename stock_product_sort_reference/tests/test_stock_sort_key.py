# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockSortKey(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.size = cls.env['product.attribute'].create({
            'name': 'Test size',
            'create_variant': 'always',
            'value_ids': [
                (0, 0, {'name': name, 'sequence': seq})
                for seq, name in enumerate(['XS', 'S', 'M', 'L', 'XL', 'XXL'])
            ],
        })
        cls.template = cls.env['product.template'].create({
            'name': 'Test sweater',
            'is_storable': True,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': cls.size.id,
                'value_ids': [(6, 0, cls.size.value_ids.ids)],
            })],
        })
        for variant in cls.template.product_variant_ids:
            size = variant.product_template_attribute_value_ids.name
            variant.default_code = '3L037-12-%s' % size
        cls.other = cls.env['product.product'].create({'name': 'Next colour', 'default_code': '3L037-120-XS'})
        cls.no_code = cls.env['product.product'].create({'name': 'AAA without reference'})

    def _sorted_codes(self, products):
        return products.sorted('stock_sort_key').mapped('default_code')

    def test_sizes_in_size_order(self):
        self.assertEqual(
            self._sorted_codes(self.template.product_variant_ids),
            ['3L037-12-XS', '3L037-12-S', '3L037-12-M', '3L037-12-L', '3L037-12-XL', '3L037-12-XXL'])

    def test_reference_before_size(self):
        # 3L037-120 comes after every size of 3L037-12, also when the
        # database collation ignores hyphens.
        products = self.template.product_variant_ids | self.other
        self.assertEqual(self._sorted_codes(products)[-1], '3L037-120-XS')
        self.env.flush_all()
        ordered = self.env['product.product'].search(
            [('id', 'in', products.ids)], order='stock_sort_key')
        self.assertEqual(ordered[-1], self.other)

    def test_without_reference_last(self):
        products = self.template.product_variant_ids | self.no_code
        self.assertEqual(products.sorted('stock_sort_key')[-1], self.no_code)

    def test_size_order_follows_attribute(self):
        xs = self.size.value_ids.filtered(lambda v: v.name == 'XS')
        xs.sequence = 99
        self.assertEqual(self._sorted_codes(self.template.product_variant_ids)[-1], '3L037-12-XS')

    def test_moves_in_reference_order(self):
        stock = self.env.ref('stock.stock_location_stock')
        customers = self.env.ref('stock.stock_location_customers')
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': stock.id,
            'location_dest_id': customers.id,
        })
        # Created in reverse order, as the lines of an order could be.
        for variant in self.template.product_variant_ids.sorted('stock_sort_key', reverse=True):
            self.env['stock.move'].create({
                'name': variant.display_name,
                'picking_id': picking.id,
                'product_id': variant.id,
                'product_uom_qty': 1,
                'location_id': stock.id,
                'location_dest_id': customers.id,
            })
        picking.invalidate_recordset(['move_ids'])
        self.assertEqual(picking.move_ids.mapped('product_id.default_code')[0], '3L037-12-XS')
        self.assertEqual(picking.move_ids.mapped('product_id.default_code')[-1], '3L037-12-XXL')

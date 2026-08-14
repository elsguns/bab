# Part of the o.s.admin add-ons.
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    barcode_block_extra_quantity = fields.Boolean(
        "Block scanning more than demanded",
        help="In the barcode app, refuse the part of a scan that would push a line above "
             "its demand. Without this, the excess silently ends up on an extra line and "
             "the transfer ships more than it asked for.\n"
             "Leave this off on receipts: a supplier delivering more than ordered is "
             "normal and has to be bookable.")

    def _get_barcode_config(self):
        # The barcode client reads its whole configuration from this dict; a
        # field that is not in here does not exist as far as the app is concerned.
        config = super()._get_barcode_config()
        config['barcode_block_extra_quantity'] = self.barcode_block_extra_quantity
        return config

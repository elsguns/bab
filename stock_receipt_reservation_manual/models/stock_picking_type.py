# Part of the o.s.admin add-ons.
from odoo import models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def _compute_hide_reservation_method(self):
        # Standard Odoo hides the method on receipts because it ignores it there.
        super()._compute_hide_reservation_method()
        self.filtered(lambda picking_type: picking_type.code == 'incoming').hide_reservation_method = False

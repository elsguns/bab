# Part of the o.s.admin add-ons.
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _is_manual_receipt(self):
        """Stock from a vendor needs no reservation: standard Odoo fills such a move in on
        every automatic assign, whatever the reservation method of its operation type."""
        self.ensure_one()
        picking_type = self.picking_type_id
        return (
            picking_type.code == 'incoming'
            and picking_type.reservation_method == 'manual'
            and self._should_bypass_reservation()
        )

    def _action_assign(self, force_qty=False):
        # Confirming the order, the scheduler, a backorder, a changed demand: all of them end up
        # here. Only Check Availability on the receipt itself sets the context key.
        if not self.env.context.get('assign_manual_receipts'):
            self = self.filtered(lambda move: not move._is_manual_receipt())
        return super()._action_assign(force_qty=force_qty)

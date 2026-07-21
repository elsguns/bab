# Part of the o.s.admin add-ons.
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Assign the delivery address its stock location code when the order
        is actually confirmed. Addresses that already have a code keep it, so
        confirming a second order for the same address changes nothing.
        Renumbering all addresses from scratch stays the job of the
        "* Stocklocatie toekennen" server action.
        """
        res = super().action_confirm()
        self.mapped('partner_shipping_id')._assign_stock_location()
        return res

    def write(self, vals):
        """When the delivery address of an already-confirmed order is changed
        to one that has no stock location code yet, assign it the next number
        in the country range. On draft orders nothing happens: the address is
        numbered at confirmation.
        """
        res = super().write(vals)
        if 'partner_shipping_id' in vals:
            confirmed = self.filtered(lambda o: o.state == 'sale')
            confirmed.mapped('partner_shipping_id')._assign_stock_location()
        return res

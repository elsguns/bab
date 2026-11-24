# Part of the o.s.admin add-ons.
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_assign(self):
        # Check Availability is a deliberate click: it may fill in a manual receipt.
        return super(StockPicking, self.with_context(assign_manual_receipts=True)).action_assign()

# Part of the o.s.admin add-ons.
from odoo import models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def action_batch(self):
        # A default favorite on the batch transfers action (e.g. grouped by operation type)
        # would replace the dashboard's filter on this operation type and list every batch.
        action = super().action_batch()
        action['context']['search_disable_custom_filters'] = True
        return action

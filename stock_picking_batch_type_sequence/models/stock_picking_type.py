# Part of the o.s.admin add-ons.
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    batch_sequence_id = fields.Many2one(
        'ir.sequence', string="Batch Sequence", copy=False,
        check_company=True,
        help="Sequence for the names of the batch transfers of this operation type. "
             "Empty: the standard batch sequence (BATCH/...).")

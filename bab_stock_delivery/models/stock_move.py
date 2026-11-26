# Part of the o.s.admin add-ons.
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    # What the slips (Productenmatrix) printed so far put on paper for this move:
    # the reserved quantity at the last slips run. The slips after a receipt print
    # the difference with the reservation now, so a second receipt of the same
    # variant only shows what it added, and a reservation moved to another
    # customer afterwards shows up at the next run (see
    # stock.picking._get_matrix_slip_quantities). Not touched when a reservation
    # changes: only a slips run sets it. copy=False: a backorder carries no paper.
    matrix_printed_qty = fields.Float(
        string="Printed on slips", digits='Product Unit of Measure',
        default=0.0, copy=False, readonly=True)

    # On a receipt move: how much of what it brought in was reserved on the open
    # picks when the receipt was validated (see stock.picking._action_done). Odoo
    # does not tie a reservation to the receipt it came from, so it is measured
    # once, as the rise of the picks' reservations during the validation.
    matrix_reserved_qty = fields.Float(
        string="Reserved for customers", digits='Product Unit of Measure',
        default=0.0, copy=False, readonly=True)

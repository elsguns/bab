# Part of the o.s.admin add-ons.
from odoo import fields, models
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    # What the slips (Productenmatrix) printed so far put on paper for this move:
    # the reserved quantity at the last slips run. The slips after a receipt print
    # the difference with the reservation now, so a second receipt of the same
    # variant only shows what it added, and a reservation moved to another
    # customer afterwards shows up at the next run (see
    # stock.picking._get_matrix_slip_quantities). Not touched when a reservation
    # changes: only a slips run sets it. copy=False: a plain copy carries no
    # paper; a backorder carries what was on paper and did not go along with the
    # validated pick (see _prepare_move_split_vals).
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

    def _prepare_move_split_vals(self, qty):
        """A pick validated with less than was on its slips: the rest goes to the
        backorder together with its place on paper, so the next slips only print
        what is really added (Els, 27/11: option B).

        Validating splits off the not-picked demand while self.quantity is what
        goes along; whatever was printed above that travels to the backorder.
        """
        vals = super()._prepare_move_split_vals(qty)
        rest = self.matrix_printed_qty - self.quantity
        if float_compare(rest, 0, precision_rounding=self.product_uom.rounding) > 0:
            vals['matrix_printed_qty'] = min(rest, qty)
        return vals

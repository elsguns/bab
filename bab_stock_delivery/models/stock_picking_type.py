# Part of the o.s.admin add-ons.
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    # Lucati (and, once approved, Vasa) lay out each receipt per hoofdproduct on
    # tables and pick from there into the customers' boxes straight away. The
    # slips must therefore come with the receipt, not with the validated pick:
    # validating the receipt reserves the waiting pick transfers, and those are
    # the slips to print. Off = the original behaviour (slips only on a done
    # pick), so switching back is just unticking this box.
    auto_print_matrix_after_receipt = fields.Boolean(
        string="Productenmatrix (briefjes) of the pick transfers",
        help="When a receipt of this type is validated, print the Productenmatrix "
             "(briefjes) of every pick transfer that has something reserved of "
             "the received hoofdproducten, limited to those hoofdproducten, and "
             "keep each slip as an attachment in the chatter of its pick "
             "transfer. While this is ticked, the slips can also be printed on a "
             "pick transfer that is not done yet.",
    )

    # Lucati: Hilde first wants to see, after a receipt, how the received goods
    # were reserved, so she can still move reservations between customers. The
    # slips then wait for the action "* Briefjes van de pickbonnen" on the receipt.
    matrix_slips_on_request = fields.Boolean(
        string="First the reservations, slips on request",
        help="Validating a receipt prints the Productenmatrix met reservaties of "
             "the received hoofdproducten instead of the slips. Once the "
             "reservations are right, the action \"* Briefjes van de pickbonnen\" "
             "on the receipt prints the slips.",
    )

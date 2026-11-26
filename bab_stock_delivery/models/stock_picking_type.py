# Part of the o.s.admin add-ons.
from odoo import _, api, fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    # Lucati (and, once approved, Vasa) lay out each receipt per hoofdproduct on
    # tables and pick from there into the customers' boxes straight away. The
    # slips must therefore come with the receipt, not with the validated pick:
    # validating the receipt reserves the waiting pick transfers, and those are
    # the slips to print. Hilde first wants to see how the received goods were
    # reserved, so she can still move reservations between customers:
    # validating prints that overview, and the slips wait for the action
    # "* Briefjes van de pickbonnen" on the receipt. Off = the original
    # behaviour (slips only on a done pick), so switching back is just
    # unticking this box.
    auto_print_matrix_after_receipt = fields.Boolean(
        string="Productenmatrix (briefjes) of the pick transfers",
        help="When a receipt of this type is validated, print the Productenmatrix "
             "met reservaties of the received hoofdproducten. Once the "
             "reservations are right, the action \"* Briefjes van de pickbonnen\" "
             "on the receipt prints the Productenmatrix (briefjes) of every pick "
             "transfer that has something reserved of those hoofdproducten and "
             "keeps each slip in the chatter of its pick transfer. While this is "
             "ticked, the slips can also be printed on a pick transfer that is "
             "not done yet.",
    )

    # Inventory Overview: done receipts whose slips were not printed yet, so
    # Hilde sees which receipts still wait for "* Briefjes van de pickbonnen".
    count_matrix_slips_to_print = fields.Integer(compute='_compute_count_matrix_slips_to_print')

    def _compute_count_matrix_slips_to_print(self):
        slip_types = self.filtered(lambda t: t.code == 'incoming' and t.auto_print_matrix_after_receipt)
        data = dict(self.env['stock.picking']._read_group(
            [('picking_type_id', 'in', slip_types.ids)] + self._matrix_slips_to_print_domain(),
            ['picking_type_id'], ['__count'],
        )) if slip_types else {}
        for picking_type in self:
            picking_type.count_matrix_slips_to_print = data.get(picking_type, 0)

    @api.model
    def _matrix_slips_to_print_domain(self):
        return [('state', '=', 'done'), ('matrix_printed', '=', False)]

    def get_action_matrix_slips_to_print(self):
        # A domain rather than a filter in the transfers' search view: such a
        # filter would show in every database using this module.
        self.ensure_one()
        action = self._get_action('stock.action_picking_tree_incoming')
        action['display_name'] = _("%s: slips to print", self.display_name)
        action['domain'] = [('picking_type_id', '=', self.id)] + self._matrix_slips_to_print_domain()
        return action

# Part of the o.s.admin add-ons.
from odoo import api, fields, models


class MatrixReprintConfirm(models.TransientModel):
    # Confirmation step shown by stock.picking.action_print_matrix when one or
    # more selected deliveries have already had their Productenmatrix printed.
    _name = 'bab.matrix.reprint.confirm'
    _description = 'Confirm reprint of the Productenmatrix'

    picking_ids = fields.Many2many('stock.picking', string="Deliveries")
    # The already-printed subset, shown in the dialog so the user sees exactly
    # which transfers would be reprinted.
    already_printed_ids = fields.Many2many(
        'stock.picking', 'bab_matrix_reprint_confirm_printed_rel',
        compute='_compute_already_printed_ids', string="Already printed")

    @api.depends('picking_ids')
    def _compute_already_printed_ids(self):
        for wizard in self:
            wizard.already_printed_ids = wizard.picking_ids.filtered('matrix_printed')

    def action_confirm(self):
        """Print everything that was selected, reprints included."""
        self.ensure_one()
        action = self.picking_ids.with_context(
            matrix_reprint_confirmed=True).action_print_matrix()
        # Without this flag the report downloads but this dialog stays open.
        action['close_on_report_download'] = True
        return action

    def action_skip_reprints(self):
        """Print only the not-yet-printed deliveries, skipping the reprints.

        The already-printed ones are left untouched. If the whole selection was
        already printed there is nothing new to print, so we just close.
        """
        self.ensure_one()
        to_print = self.picking_ids.filtered(lambda p: not p.matrix_printed)
        if not to_print:
            return {'type': 'ir.actions.act_window_close'}
        # to_print has no already-printed picking, so action_print_matrix prints
        # straight away without re-opening this wizard.
        action = to_print.action_print_matrix()
        action['close_on_report_download'] = True
        return action

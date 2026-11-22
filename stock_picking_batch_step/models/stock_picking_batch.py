# Part of the o.s.admin add-ons.
from odoo import api, fields, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    # Odoo keeps no link between the batches of two steps (pick -> ship, or
    # pick -> pack -> ship): each step batches its own transfers. The link
    # exists one level down, between the stock moves of consecutive transfers,
    # so the batches of the previous and next step are read from there.
    previous_batch_ids = fields.Many2many(
        'stock.picking.batch', string="Previous Step",
        compute='_compute_step_batch_ids',
        help="Batches holding the transfers of the step before this one.")
    next_batch_ids = fields.Many2many(
        'stock.picking.batch', string="Next Step",
        compute='_compute_step_batch_ids',
        help="Batches holding the transfers of the step after this one.")
    previous_batch_count = fields.Integer(compute='_compute_step_batch_ids')
    next_batch_count = fields.Integer(compute='_compute_step_batch_ids')

    # Through picking_ids, not the batch's own move_ids: that one is computed
    # and not searchable, so the ORM could not tell which batch to recompute.
    @api.depends('picking_ids.move_ids.move_orig_ids.picking_id.batch_id',
                 'picking_ids.move_ids.move_dest_ids.picking_id.batch_id')
    def _compute_step_batch_ids(self):
        for batch in self:
            moves = batch.picking_ids.move_ids
            previous = moves.move_orig_ids.picking_id.batch_id - batch
            following = moves.move_dest_ids.picking_id.batch_id - batch
            batch.previous_batch_ids = previous
            batch.next_batch_ids = following
            batch.previous_batch_count = len(previous)
            batch.next_batch_count = len(following)

    def action_view_previous_batches(self):
        self.ensure_one()
        return self._action_view_step_batches(self.previous_batch_ids)

    def action_view_next_batches(self):
        self.ensure_one()
        return self._action_view_step_batches(self.next_batch_ids)

    def _action_view_step_batches(self, batches):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'stock_picking_batch.stock_picking_batch_action')
        if len(batches) == 1:
            action.update(views=[(False, 'form')], res_id=batches.id)
        else:
            action.update(domain=[('id', 'in', batches.ids)], context={})
        return action

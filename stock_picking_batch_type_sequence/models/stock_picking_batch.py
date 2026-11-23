# Part of the o.s.admin add-ons.
from odoo import api, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    @api.model_create_multi
    def create(self, vals_list):
        # Name it before super(): the standard create only fills a name that is still '/'.
        type_ids = {vals['picking_type_id'] for vals in vals_list
                    if vals.get('picking_type_id') and not vals.get('is_wave')
                    and vals.get('name', '/') == '/'}
        sequence_by_type = {
            picking_type.id: picking_type.batch_sequence_id
            for picking_type in self.env['stock.picking.type'].browse(type_ids)
            if picking_type.batch_sequence_id
        }
        for vals in vals_list:
            sequence = (not vals.get('is_wave') and vals.get('name', '/') == '/'
                        and sequence_by_type.get(vals.get('picking_type_id')))
            if sequence:
                vals['name'] = sequence.sudo().next_by_id() or '/'
        return super().create(vals_list)

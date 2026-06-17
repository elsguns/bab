# Part of the o.s.admin add-ons.
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportDeliverySlipMatrix(models.AbstractModel):
    # Render model backing the Productenmatrix report
    # (report_name = bab_stock_delivery.report_deliveryslip_matrix).
    _name = 'report.bab_stock_delivery.report_deliveryslip_matrix'
    _description = 'Productenmatrix delivery report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Build the report values, but only for outgoing deliveries.

        The Productenmatrix is a packing/delivery slip and only makes sense for
        outgoing transfers. Odoo report bindings carry no per-record visibility,
        so we can't hide the Print entry on incoming/internal pickings; instead we
        refuse to render as soon as a non-outgoing picking is in the selection,
        with a clear message naming the offending transfers.
        """
        pickings = self.env['stock.picking'].browse(docids)
        wrong_type = pickings.filtered(lambda p: p.picking_type_id.code != 'outgoing')
        if wrong_type:
            raise UserError(_(
                "The Productenmatrix can only be printed for outgoing deliveries.\n"
                "These transfers have a different operation type: %s",
                ", ".join(wrong_type.mapped('name')),
            ))
        # Mark the deliveries as printed so a later print run can warn before a
        # reprint (see stock.picking.action_print_matrix). Runs on every render
        # path, so the flag stays correct even if the report is reached directly.
        pickings.filtered(lambda p: not p.matrix_printed).matrix_printed = True
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            'data': data,
        }

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
        """Build the report values, but only for completed pick transfers.

        The Productenmatrix is cut into slips that travel with the picked goods,
        so it only makes sense once the warehouse's pick step is validated. Odoo
        report bindings carry no per-record visibility, so we can't hide the Print
        entry on other transfers; instead we refuse to render as soon as the
        selection holds anything else, naming the offending transfers and why they
        don't qualify.

        The pick operation type is read from the transfer's own warehouse rather
        than matched on a code or a fixed id: every warehouse (Babimex, bol.com,
        Vasa) has its own pick type, and its code is 'internal' like that of any
        other internal transfer.
        """
        pickings = self.env['stock.picking'].browse(docids)
        refused = []
        for picking in pickings:
            if picking.picking_type_id != picking.picking_type_id.warehouse_id.pick_type_id:
                refused.append(_("%s (not a pick transfer)", picking.name))
            elif picking.state != 'done':
                refused.append(_("%s (not done yet)", picking.name))
        if refused:
            raise UserError(_(
                "The Productenmatrix can only be printed for pick transfers that are done.\n%s",
                "\n".join(refused),
            ))
        # Mark the transfers as printed so a later print run can warn before a
        # reprint (see stock.picking.action_print_matrix). Runs on every render
        # path, so the flag stays correct even if the report is reached directly.
        pickings.filtered(lambda p: not p.matrix_printed).matrix_printed = True
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            'data': data,
        }

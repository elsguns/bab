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

        Exception: in a warehouse whose receipts print the slips (see
        stock.picking.type.auto_print_matrix_after_receipt) a pick that is not
        done yet is accepted too, since the slips then follow the reservation.

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
        if not docids and data:
            # A report action that carries data (the slips printed after a
            # receipt) is downloaded by the web client as /report/pdf/<name>?options=...
            # without ids in the URL: the picks only travel in the action's context.
            docids = (data.get('context') or {}).get('active_ids')
        pickings = self.env['stock.picking'].browse(docids)
        # One query for the whole selection, not one per pick.
        slip_warehouses = pickings.picking_type_id.warehouse_id._get_matrix_slip_warehouses()
        refused = []
        for picking in pickings:
            if picking.picking_type_id != picking.picking_type_id.warehouse_id.pick_type_id:
                refused.append(_("%s (not a pick transfer)", picking.name))
            elif picking.state != 'done' and not (
                    picking.state not in ('draft', 'cancel')
                    and picking.picking_type_id.warehouse_id in slip_warehouses):
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
        # The slips printed after a receipt only carry that receipt's variants
        # and only what changed since the previous slips, see
        # stock.picking._print_matrix_after_receipt, which also records what
        # they printed.
        if data and data.get('matrix_product_ids'):
            pickings = pickings.with_context(
                matrix_product_ids=data['matrix_product_ids'],
                matrix_slip_changes=data.get('matrix_slip_changes', False))
        else:
            # A full slip of the pick: everything reserved is now on paper. Only
            # the open moves matter: the slips after a receipt only look at open
            # picks, so a done pick (the only kind a warehouse without slips
            # after a receipt prints) writes nothing. One write per quantity,
            # not one per move.
            open_moves = pickings.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            for quantity, moves in open_moves.grouped('quantity').items():
                moves.matrix_printed_qty = quantity
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            # One article per pick so Odoo can split the PDF per pick, see the
            # report template.
            'split_per_picking': bool(data and data.get('matrix_split_per_picking')),
            'data': data,
        }

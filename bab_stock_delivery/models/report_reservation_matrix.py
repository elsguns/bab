# Part of the o.s.admin add-ons.
from odoo import api, models


class ReportReservationMatrix(models.AbstractModel):
    # Render model backing the "Productenmatrix met reservaties" report
    # (report_name = bab_stock_delivery.report_reservation_matrix).
    _name = 'report.bab_stock_delivery.report_reservation_matrix'
    _description = 'Productenmatrix met reservaties'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Build the reservation matrix across the selected deliveries.

        One matrix per hoofdproduct (kleur rows x maat columns) with, per cell,
        the reserved quantity, a signed shortage/surplus figure and the incoming
        quantity. The heavy lifting lives in
        stock.picking._get_reservation_matrix_blocks; pickings without matching
        variant moves simply contribute nothing there. Like the overview this
        report may be printed as often as needed (no print-once guard).
        """
        if not docids and data:
            # Printed after a receipt: the web client downloads a report action
            # with data without ids in the URL, the picks only travel in the
            # action's context (same as the slips, see report_delivery_matrix).
            docids = (data.get('context') or {}).get('active_ids')
        pickings = self.env['stock.picking'].browse(docids)
        if data and data.get('matrix_template_ids'):
            pickings = pickings.with_context(matrix_template_ids=data['matrix_template_ids'])
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            'blocks': pickings._get_reservation_matrix_blocks(),
            'data': data,
        }

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
        pickings = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            'blocks': pickings._get_reservation_matrix_blocks(),
            'data': data,
        }

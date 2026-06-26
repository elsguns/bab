# Part of the o.s.admin add-ons.
from odoo import api, models


class ReportProductOverview(models.AbstractModel):
    # Render model backing the Productenoverzicht report
    # (report_name = bab_stock_delivery.report_product_overview).
    _name = 'report.bab_stock_delivery.report_product_overview'
    _description = 'Productenmatrix per kleur en klant'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Build the customer×size overview across the selected deliveries.

        Unlike the Productenmatrix this report may be printed as often as needed,
        so there is no print-once guard here, and it can be printed from the pick
        step as well as the outgoing transfer. The heavy lifting (bucketing the
        ordered quantities per hoofdproduct+kleur) lives in
        stock.picking._get_customer_matrix_blocks; pickings without a linked sales
        order simply contribute nothing there.
        """
        pickings = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            'blocks': pickings._get_customer_matrix_blocks(),
            'data': data,
        }

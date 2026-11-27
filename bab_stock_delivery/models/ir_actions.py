# Part of the o.s.admin add-ons.
from odoo import api, models
from odoo.tools import frozendict


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    # The two Productenmatrix reports, in the order they close the Print menu.
    _MATRIX_PRINT_REPORTS = (
        'bab_stock_delivery.action_report_reservation_matrix',
        'bab_stock_delivery.action_report_product_overview',
    )

    @api.model
    def _get_bindings(self, model_name):
        """Keep the two Productenmatrix reports next to each other, last in Print.

        Odoo lists the Print menu by action id, so a report module installed
        later (delivery_iot: Verzendlabels, Verzenddocumenten) would land between
        or after them. Reordering here keeps the records themselves, and with
        them any link made to one of them, instead of re-creating them on every
        update.
        """
        result = super()._get_bindings(model_name)
        reports = result.get('report')
        if model_name != 'stock.picking' or not reports:
            return result
        matrix_ids = []
        for xmlid in self._MATRIX_PRINT_REPORTS:
            report = self.env.ref(xmlid, raise_if_not_found=False)
            if report:
                matrix_ids.append(report.id)
        matrix = sorted((r for r in reports if r['id'] in matrix_ids), key=lambda r: matrix_ids.index(r['id']))
        if not matrix:
            return result
        others = [r for r in reports if r['id'] not in matrix_ids]
        return frozendict(result, report=tuple(others + matrix))

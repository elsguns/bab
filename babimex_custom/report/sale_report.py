# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'

    commercial_name_id = fields.Many2one(
        comodel_name='commercial.name',
        readonly=True
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['commercial_name_id'] = 's.commercial_name_id'
        return res

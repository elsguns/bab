# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    commercial_name_id = fields.Many2one(
        comodel_name='commercial.name',
        string="Commercial Name"
    )

    def _select(self) -> SQL:
        return SQL("%s, move.commercial_name_id as commercial_name_id", super()._select())

# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, _, api, fields, models, Command


class AccountMove(models.Model):
    _inherit = 'account.move'

    commercial_name_id = fields.Many2one(
        related='partner_id.commercial_name_id',
        string='Commercial Name',
        store=True
    )

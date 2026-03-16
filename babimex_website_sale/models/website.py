# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    show_line_subtotals_tax_selection_public_user = fields.Selection(
        string="Display Product Prices (Public/Not logged in User)",
        selection=[
            ('tax_excluded', "Tax Excluded"),
            ('tax_included', "Tax Included"),
        ],
        required=True,
        default='tax_included',
    )

    show_line_subtotals_tax_selection_log_in_user = fields.Selection(
        string="Display Product Prices (Logged in User)",
        selection=[
            ('tax_excluded', "Tax Excluded"),
            ('tax_included', "Tax Included"),
        ],
        required=True,
        default='tax_excluded',
    )

    # Override to make field compute based on log in user
    show_line_subtotals_tax_selection = fields.Selection(
        string="Line Subtotals Tax Display",
        compute="_compute_show_line_subtotals_tax_selection",
        store=False,
        selection=[
            ('tax_excluded', "Tax Excluded"),
            ('tax_included', "Tax Included"),
        ],
    )

    def _compute_show_line_subtotals_tax_selection(self):
        for website in self:
            # Set tax_included for website users
            if self.env.user._is_public():
                website.show_line_subtotals_tax_selection = website.show_line_subtotals_tax_selection_public_user
            else:
                website.show_line_subtotals_tax_selection = website.show_line_subtotals_tax_selection_log_in_user

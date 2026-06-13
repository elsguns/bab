# Part of the o.s.admin add-ons.
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Babimex stock location code, shown before the customer name on the
    # Productenmatrix delivery report.
    stock_location = fields.Integer(string="Stock Location")

# Part of the o.s.admin add-ons.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Contacts are shared between the companies (res.partner.company_id is
    # empty), so nothing stops an order of one company from consuming numbers
    # out of the country ranges that another company prints on its
    # "Productenmatrix". Only the companies flagged here hand out numbers.
    stock_location_numbering = fields.Boolean(
        string="Assign stock locations",
        help="Give the delivery address of a confirmed sales order the next "
             "stock location number in its country range. Leave this off for "
             "companies that do not print stock location codes.",
    )

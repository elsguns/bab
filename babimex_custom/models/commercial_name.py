from odoo import models, fields


class CommercialName(models.Model):
    _name = 'commercial.name'
    _description = 'Commercial Name'

    name = fields.Char(
        string='Name',
        required=True
    )

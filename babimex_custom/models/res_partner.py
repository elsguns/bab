# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_purchasing_department = fields.Boolean(
        string="Is Purchasing Department",
        copy=False
    )

    commercial_name_id = fields.Many2one(
        'commercial.name',
        string='Commercial Name',
    )

    @api.constrains('commercial_name_id', 'create_uid')
    def _check_commercial_name_id(self):
        """
            - If the partner is different from its `commercial_partner_id` and the commercial partner has a `commercial_name_id`,
              it assigns the same `commercial_name_id` to the current partner.
            - If the partner has child partners (`child_ids`), their `commercial_name_id` is updated:
              - Set to the parent's `commercial_name_id` if it exists.
              - Set to `False` otherwise.
        """
        for partner in self:
            if partner != partner.commercial_partner_id and partner.commercial_partner_id.commercial_name_id != partner.commercial_name_id:
                partner.commercial_name_id = partner.commercial_partner_id.commercial_name_id.id
            if partner.child_ids:
                if partner.commercial_name_id:
                    partner.child_ids.write({
                        'commercial_name_id': partner.commercial_name_id.id
                    })
                else:
                    partner.child_ids.write({
                        'commercial_name_id': False
                    })

# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, _, api, fields, models, Command


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commercial_name_id = fields.Many2one(
        related='partner_id.commercial_name_id',
        string='Commercial Name',
        store=True
    )

    # def _get_buyer_and_purchasing_contacts(self):
    #     """
    #     Get the buyer partner and associated purchasing department contacts
    #     """
    #     self.ensure_one()
    #     buyer_partner_id = self.partner_id
    #     purchasing_dept_ids = self.env['res.partner'].search([
    #         ('parent_id', 'in', [self.partner_id.id, self.partner_id.parent_id.id]),
    #         ('is_purchasing_department', '=', True),
    #     ])
    #     return buyer_partner_id | purchasing_dept_ids
    #
    # def _send_order_notification_mail(self, mail_template):
    #     """
    #     Send a mail to the customer
    #     """
    #     self.ensure_one()
    #     if not mail_template:
    #         return
    #     if self.env.su:
    #         self = self.with_user(SUPERUSER_ID)
    #     if self.website_id:
    #         buyer_partner_id = self._get_buyer_and_purchasing_contacts()
    #         self.with_context(force_send=True).message_post_with_source(
    #             mail_template,
    #             email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
    #             subtype_xmlid='mail.mt_comment',
    #             partner_ids=buyer_partner_id.ids
    #         )
    #     else:
    #         return super()._send_order_notification_mail(mail_template)
    #
    # def action_quotation_send(self):
    #     result = super().action_quotation_send()
    #     context = result.get('context', {})
    #     buyer_partner_id = self._get_buyer_and_purchasing_contacts()
    #     context.update({
    #         "default_partner_ids": [Command.link(partner.id) for partner in buyer_partner_id]
    #     })
    #     return result

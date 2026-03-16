
from odoo import _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleBabimex(WebsiteSale):


    def _prepare_checkout_page_values(self, order_sudo, **query_params):
        """ Override of `website_sale` to remove logged in user's address """
        res = super()._prepare_checkout_page_values(order_sudo, **query_params)
        PartnerSudo = order_sudo.partner_id.with_context(show_address=1)
        commercial_partner_sudo = order_sudo.partner_id.commercial_partner_id
        billing_partners_sudo = PartnerSudo.search([
            ('id', 'child_of', commercial_partner_sudo.ids),
            '|',
            ('type', 'in', ['invoice', 'other']),
            ('id', '=', commercial_partner_sudo.id),
        ], order='id desc')
        delivery_partners_sudo = PartnerSudo.search([
            ('id', 'child_of', commercial_partner_sudo.ids),
            '|',
            ('type', 'in', ['delivery', 'other']),
            ('id', '=', commercial_partner_sudo.id),
        ], order='id desc')

        if order_sudo.partner_id != commercial_partner_sudo:  # Child of the commercial partner.
            # Don't display the commercial partner's addresses if they are not complete, as its
            # children can't edit them.
            if not self._check_billing_address(commercial_partner_sudo):
                billing_partners_sudo = billing_partners_sudo.filtered(
                    lambda p: p.id != commercial_partner_sudo.id
                )
            if not self._check_delivery_address(commercial_partner_sudo):
                delivery_partners_sudo = delivery_partners_sudo.filtered(
                    lambda p: p.id != commercial_partner_sudo.id
                )

        res['billing_addresses'] = billing_partners_sudo
        res['delivery_addresses'] = delivery_partners_sudo
        return res

    def _check_cart_and_addresses(self, order_sudo):
        """ Removed the _check_addresses to avoid the redirection to the address page"""
        if redirection := self._check_cart(order_sudo):
            return redirection

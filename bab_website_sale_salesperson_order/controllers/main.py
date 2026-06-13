# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.bab_website_sale_salesperson_order.models.website import SESSION_KEY


class WebsiteSale(WebsiteSale):

    def _is_salesperson(self):
        return request.env.user.has_group('sales_team.group_sale_salesman')

    def _force_order_for_partner(self, order_sudo):
        """Force the cart onto the selected customer. The cart is already
        realigned in website.sale_get_order, but checkout resolves the order
        through several paths, so we re-assert it defensively here."""
        partner_sudo = request.website._get_order_for_partner()
        if partner_sudo and order_sudo.partner_id != partner_sudo:
            order_sudo.write({
                'partner_id': partner_sudo.id,
                'partner_invoice_id': partner_sudo.id,
                'partner_shipping_id': partner_sudo.id,
            })

    def _prepare_checkout_page_values(self, order_sudo, **kwargs):
        self._force_order_for_partner(order_sudo)
        return super()._prepare_checkout_page_values(order_sudo, **kwargs)

    def _check_addresses(self, order_sudo):
        self._force_order_for_partner(order_sudo)
        return super()._check_addresses(order_sudo)

    def _prepare_address_update(self, order_sudo, partner_id=None, address_type=None):
        partner_sudo = request.website._get_order_for_partner()
        if partner_sudo:
            return partner_sudo, address_type or 'contact'
        return super()._prepare_address_update(order_sudo, partner_id=partner_id, address_type=address_type)

    @http.route('/shop/select_customer', type='http', auth='user', website=True, sitemap=False)
    def shop_select_customer(self, **post):
        # Only salespersons (Sales group) may order on behalf of a customer.
        if not self._is_salesperson():
            return request.redirect('/shop')
        values = {
            # Only the contacts for whom the logged-in user is the Salesperson
            # (res.partner.user_id), so each salesperson sees their own customers.
            'customers': request.env['res.partner'].sudo().search([
                ('user_id', '=', request.env.user.id),
            ]),
            'selected_partner': request.website._get_order_for_partner(),
        }
        return request.render('bab_website_sale_salesperson_order.shop_select_customer', values)

    @http.route('/shop/set_customer', type='http', auth='user', website=True, sitemap=False)
    def shop_set_customer(self, partner_id=None, **post):
        # The customer's pricelist / fiscal position are applied through the
        # website model overrides, so we only need to remember the selection.
        if not self._is_salesperson():
            return request.redirect('/shop')
        if partner_id:
            request.session[SESSION_KEY] = int(partner_id)
            # Drop any pricelist the previous customer's shop session left behind,
            # so the shop grid (and a fresh cart) recompute from the new customer
            # instead of re-pinning the old customer's pricelist.
            request.session.pop('website_sale_current_pl', None)
            request.session.pop('website_sale_selected_pl_id', None)
        return request.redirect('/shop')

    @http.route('/shop/confirmation', type='http', auth='public', website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        # Clear the selection once the order is confirmed so the next cart starts
        # fresh (the customer <select> is re-enabled on /shop). Also drop the
        # shop-session pricelist so the next customer is not priced with this one.
        request.session.pop(SESSION_KEY, None)
        request.session.pop('website_sale_current_pl', None)
        request.session.pop('website_sale_selected_pl_id', None)
        return super().shop_payment_confirmation(**post)

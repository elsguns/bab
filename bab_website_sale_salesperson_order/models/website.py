# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request

# Session key holding the id of the customer a salesperson is ordering for.
# Shared with the controller so there is a single source of truth.
SESSION_KEY = 'website_sale_order_for_partner_id'


class Website(models.Model):
    _inherit = 'website'

    def _get_order_for_partner(self):
        """Return the customer the salesperson selected to order for, as a sudo
        recordset, or an empty recordset when nothing is selected (or when there
        is no active request)."""
        partner_id = request and request.session.get(SESSION_KEY)
        if partner_id:
            return self.env['res.partner'].sudo().browse(partner_id)
        return self.env['res.partner']

    def _get_order_for_partner_pricelist(self):
        """Pricelist to use when ordering on behalf of the selected customer.

        We must NOT use partner.property_product_pricelist directly: in a website
        request website_sale filters that resolution to pricelists that are
        "available on the website" (see website_sale's
        _get_partner_pricelist_multi_filter_hook). A customer whose assigned
        pricelist is not flagged for the website would therefore be silently
        re-priced with a website pricelist instead — exactly the deviation this
        module must avoid. So when the customer has an explicitly assigned
        pricelist (specific_property_product_pricelist, a stored field that is
        not website-filtered) we honour it as-is; otherwise we fall back to the
        standard resolved pricelist.
        """
        partner_sudo = self._get_order_for_partner()
        if not partner_sudo:
            return self.env['product.pricelist']
        specific = partner_sudo.specific_property_product_pricelist.sudo().filtered('active')
        return specific[:1] or partner_sudo.property_product_pricelist.sudo()

    def sale_get_order(self, force_create=False):
        # website_sale realigns the cart partner to the logged-in user whenever
        # they differ (see the base sale_get_order -> _update_address call). For
        # a salesperson shopping on behalf of a customer that resets the cart
        # (and, through _compute_pricelist_id, the pricelist) back to the
        # salesperson. Re-apply the selected customer so the cart, its pricelist
        # and its fiscal position stay aligned with the salesperson's pick.
        order_sudo = super().sale_get_order(force_create=force_create)
        partner_sudo = self._get_order_for_partner()
        if order_sudo and partner_sudo:
            if order_sudo.partner_id != partner_sudo:
                order_sudo._update_address(partner_sudo.id, ['partner_id'])
            # An order placed on behalf of a customer must be priced with THAT
            # customer's pricelist. Both cart creation (website.pricelist_id) and
            # _update_address can leave the salesperson's / a stale shop-session /
            # the salesperson's last-cart pricelist on the order, so re-assert the
            # customer's pricelist here. Without this a B2C customer can end up
            # paying a B2B price carried over from the previous selection.
            pricelist_sudo = self._get_order_for_partner_pricelist()
            if (order_sudo.state == 'draft'
                    and pricelist_sudo
                    and order_sudo.pricelist_id != pricelist_sudo):
                order_sudo._cart_update_pricelist(pricelist_id=pricelist_sudo.id)
        return order_sudo

    def _prepare_sale_order_values(self, partner_sudo):
        values = super()._prepare_sale_order_values(partner_sudo)
        order_for_partner = self._get_order_for_partner()
        if order_for_partner:
            values.update({
                'partner_id': order_for_partner.id,
                'partner_invoice_id': order_for_partner.id,
                'partner_shipping_id': order_for_partner.id,
                # Record the shopping salesperson as the order's standard
                # Salesperson; website_sale only fills user_id on confirmation
                # when it is still empty (see sale.order._compute_user_id), so
                # this assignment sticks.
                'user_id': self.env.user.id,
            })
            # Create the cart already priced for the customer. super() copied
            # website.pricelist_id (the salesperson's / a stale shop pricelist);
            # since partner_id is set to the customer in the same create(), the
            # stock _compute_pricelist_id won't run, so an explicit value here is
            # the only thing that keeps the cart aligned with its customer.
            pricelist_sudo = self._get_order_for_partner_pricelist()
            if pricelist_sudo:
                values['pricelist_id'] = pricelist_sudo.id
        return values

    def _get_current_pricelist(self):
        # Selecting a customer always means ordering in that customer's name, so
        # the shop (product grid/detail) shows that customer's pricelist, even
        # before a cart exists. Once a cart exists it stays aligned via
        # sale_get_order + the partner-driven compute.
        pricelist_sudo = self._get_order_for_partner_pricelist()
        if pricelist_sudo:
            return pricelist_sudo
        return super()._get_current_pricelist()

    def _get_current_fiscal_position(self):
        # Mirror of the pricelist override: taxes always follow the selected
        # customer instead of the logged-in salesperson.
        partner_sudo = self._get_order_for_partner()
        if partner_sudo:
            fpos_sudo = self.env['account.fiscal.position'].sudo()._get_fiscal_position(partner_sudo)
            if fpos_sudo:
                return fpos_sudo
        return super()._get_current_fiscal_position()

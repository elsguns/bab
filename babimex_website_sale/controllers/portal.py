from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class MyCustomerPortal(CustomerPortal):

    @http.route()
    def account(self, redirect=None, **post):
        if request.env.user.has_group('base.group_portal'):
            return request.redirect('/my/home')
        return super(MyCustomerPortal, self).account(redirect, **post)

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _send_payment_succeeded_for_order_mail(self):
        """
        MFM Task: 5028
        If order is paid via Wire Transfer, Do not send email
        """
        mail_template = self.env.ref(
            'sale.mail_template_sale_payment_executed', raise_if_not_found=False
        )
        for order in self:
            transaction = order.transaction_ids.sudo().filtered(lambda tx: tx.provider_code == 'custom')
            if not transaction:
                order._send_order_notification_mail(mail_template)

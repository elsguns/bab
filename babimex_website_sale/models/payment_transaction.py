from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _post_process(self):

        result = super()._post_process()
        """
        MFM Task: 5028
        If order is paid via Wire Transfer, confirm the sales order
        """
        for pending_tx in self:
            sales_orders = pending_tx.sale_order_ids.filtered(lambda so: so.state == 'sent')
            for order in sales_orders:
                if pending_tx.provider_code == 'custom':
                    order.with_context(send_email=True).action_confirm()
        return result

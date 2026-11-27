# Part of the o.s.admin add-ons.
from odoo import models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def _get_matrix_slip_warehouses(self):
        """The warehouses among these whose picks may get their slips before done.

        That is the case as soon as one receipt type of the warehouse prints the
        slips after a receipt: the slips then follow the reservation, not the
        validated pick. Hilde's own print action relies on the same rule, so it
        keeps working on those picks too. One query for all warehouses.
        """
        if not self:
            return self
        return self.env['stock.picking.type'].search([
            ('warehouse_id', 'in', self.ids),
            ('code', '=', 'incoming'),
            ('auto_print_matrix_after_receipt', '=', True),
        ]).warehouse_id
